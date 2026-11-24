{
  description = "Standalone locked offline-verifiable workspace, isolated eval shells, and test closure for artagon-skills-eval";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-26.05";

  outputs = { self, nixpkgs }:
    let
      lib = nixpkgs.lib;
      systems = [ "aarch64-darwin" "x86_64-darwin" "x86_64-linux" "aarch64-linux" ];
      forAllSystems = lib.genAttrs systems;
      flakeLock = builtins.fromJSON (builtins.readFile ./flake.lock);
      lockedReceipt = builtins.fromJSON (builtins.readFile ./nix/locked-versions.json);

      # ADR-0006 Layer 2: eval-time forbidden-file guard against dirty path:. checkouts
      # or accidentally git-added secrets/private state directories.
      forbiddenRootNames = [
        ".env"
        ".venv"
        ".beads"
        ".ntm"
        "scratch"
        "logs"
        "candidates"
        "results"
        "holdouts"
        "private"
        "auth"
      ];
      rootEntries = builtins.attrNames (builtins.readDir ./.);
      forbiddenHits = builtins.filter (name: builtins.elem name forbiddenRootNames) rootEntries;
      _assertCleanSource =
        assert forbiddenHits == []
          || builtins.throw "ADR-0006 forbidden paths present in flake source: ${builtins.concatStringsSep ", " forbiddenHits}. Use tracked git trees or the O_NOFOLLOW stager.";
        true;

      # Metered API-key / BYOK variables scrubbed when entering isolated eval shells
      # (parity with artagon_eval_core.domain.billing.METERED_BILLING_ENV_VARS).
      meteredEnvVars = [
        "ANTHROPIC_API_KEY"
        "ANTHROPIC_AUTH_TOKEN"
        "ANTHROPIC_BASE_URL"
        "CLAUDE_CODE_USE_BEDROCK"
        "CLAUDE_CODE_USE_VERTEX"
        "CLAUDE_CODE_USE_FOUNDRY"
        "OPENAI_API_KEY"
        "OPENAI_BASE_URL"
        "OPENAI_ORG_ID"
        "AZURE_OPENAI_API_KEY"
        "GEMINI_API_KEY"
        "GOOGLE_API_KEY"
        "GOOGLE_GENAI_USE_VERTEXAI"
        "COPILOT_PROVIDER_API_KEY"
        "COPILOT_PROVIDER_BASE_URL"
        "COPILOT_PROVIDER_TYPE"
        "COPILOT_PROVIDER_WIRE_API"
        "GITHUB_COPILOT_API_TOKEN"
        "COPILOT_API_KEY"
        "COPILOT_TOKEN"
        "KIMI_API_KEY"
        "MOONSHOT_API_KEY"
        "OPENROUTER_API_KEY"
        "DAYTONA_API_KEY"
        "EVOSKILL_CC_TOKEN_FILE"
      ];

      perSystem = system:
        let
          pkgs = import nixpkgs { inherit system; };
          fs = pkgs.lib.fileset;
          python = pkgs.python312;
          py = pkgs.python312Packages;

          # ADR-0006 Layer 2: explicit lib.fileset clean-source slices per derivation
          coreSrc = fs.toSource {
            root = ./packages/artagon-eval-core;
            fileset = fs.unions [
              ./packages/artagon-eval-core/pyproject.toml
              ./packages/artagon-eval-core/src
            ];
          };

          skillsSrc = fs.toSource {
            root = ./packages/artagon-eval-skills;
            fileset = fs.unions [
              ./packages/artagon-eval-skills/pyproject.toml
              ./packages/artagon-eval-skills/src
            ];
          };

          umbrellaSrc = fs.toSource {
            root = ./.;
            fileset = fs.unions [
              ./pyproject.toml
              ./README.md
              ./src
            ];
          };

          skilloptAdapterSrc = fs.toSource {
            root = ./packages/artagon-eval-skillopt;
            fileset = fs.unions [
              ./packages/artagon-eval-skillopt/pyproject.toml
              ./packages/artagon-eval-skillopt/src
            ];
          };

          offlineTestSrc = fs.toSource {
            root = ./.;
            fileset = fs.unions [
              ./pyproject.toml
              ./README.md
              ./nix/locked-versions.json
              ./src
              ./packages/artagon-eval-core
              ./packages/artagon-eval-skills
              ./tests
            ];
          };

          # -----------------------------------------------------------------
          # 1. Pure-Python Core Derivations Not Yet in Pinned nixos-26.05
          #    SRI hashes byte-verified via `nix store prefetch-file --json`.
          # -----------------------------------------------------------------

          expressionPkg = py.buildPythonPackage rec {
            pname = "expression";
            version = "6.0.1";
            pyproject = true;
            src = pkgs.fetchurl {
              url = "https://files.pythonhosted.org/packages/source/e/expression/expression-${version}.tar.gz";
              hash = "sha256-iRZJP25jkqQT8TCWryCZ7EP45DMCLxmGJ4j2G3CLFDU=";
            };
            build-system = [ py.hatchling ];
            dependencies = [ py.typing-extensions ];
            optional-dependencies = {
              pydantic = [ py.pydantic ];
            };
            doCheck = false;
            pythonImportsCheck = [ "expression" "expression.collections" ];
            meta = {
              description = "Practical functional programming for Python 3.12+";
              license = pkgs.lib.licenses.mit;
            };
          };

          skillsRefPkg = py.buildPythonPackage rec {
            pname = "skills-ref";
            version = "0.1.1";
            pyproject = true;
            src = pkgs.fetchurl {
              url = "https://files.pythonhosted.org/packages/source/s/skills_ref/skills_ref-${version}.tar.gz";
              hash = "sha256-a0AMpuAEm+YtygFn/5Q7onRf1n77N/u6TQ7jQfzNJpU=";
            };
            build-system = [ py.hatchling ];
            dependencies = [
              py.click
              py.strictyaml
            ];
            doCheck = false;
            pythonImportsCheck = [ "skills_ref" "skills_ref.parser" "skills_ref.validator" ];
            meta = {
              description = "Reference library for the Agent Skills specification (agentskills.io)";
              license = pkgs.lib.licenses.asl20;
            };
          };

          skilloptUpstreamPkg = py.buildPythonPackage rec {
            pname = "skillopt";
            version = "0.2.0";
            pyproject = true;
            src = pkgs.fetchurl {
              url = "https://files.pythonhosted.org/packages/source/s/skillopt/skillopt-${version}.tar.gz";
              hash = "sha256-2fBHM21NE5NvJliWd0Btt330OJf6I915c/ga/3kHxOQ=";
            };
            build-system = [ py.setuptools py.wheel ];
            dependencies = with py; [
              openai
              pyyaml
              numpy
              openpyxl
              azure-identity
              azure-core
              httpx
            ];
            doCheck = false;
            pythonImportsCheck = [ "skillopt_sleep" ];
            meta = {
              description = "Microsoft SkillOpt 0.2.0 (pinned reviewed source tree)";
              license = pkgs.lib.licenses.mit;
            };
          };

          # -----------------------------------------------------------------
          # 2. Core Locked Dependency Sets (nixos-26.05 + thin derivations)
          # -----------------------------------------------------------------
          coreRuntimeDeps = (with py; [
            click
            detect-secrets
            duckdb
            jinja2
            jmespath
            jsonschema
            msgspec
            opentelemetry-proto
            packaging
            pluggy
            protobuf
            pyarrow
            pydantic
            pydantic-settings
            pyyaml
            rfc8785
            rpds-py
            structlog
            tomlkit
            typer
            typing-extensions
          ]) ++ [
            expressionPkg
          ];

          skillsRuntimeDeps = [
            py.strictyaml
            skillsRefPkg
          ];

          allCoreRuntimeDeps = coreRuntimeDeps ++ skillsRuntimeDeps;

          # -----------------------------------------------------------------
          # 3. Workspace Member Builds (artagon-eval-core -> skills -> umbrella)
          # -----------------------------------------------------------------
          evalCorePkg = py.buildPythonPackage {
            pname = "artagon-eval-core";
            version = "0.2.0";
            pyproject = true;
            src = coreSrc;
            build-system = [ py.hatchling ];
            pythonRelaxDeps = true;
            dependencies = coreRuntimeDeps;
            doCheck = false;
            pythonImportsCheck = [
              "artagon_eval_core"
              "artagon_eval_core.domain"
              "artagon_eval_core.ports"
              "artagon_eval_core.runtime"
              "artagon_eval_core.plugins"
              "artagon_eval_core.shims.wire"
            ];
          };

          evalSkillsPkg = py.buildPythonPackage {
            pname = "artagon-eval-skills";
            version = "0.2.0";
            pyproject = true;
            src = skillsSrc;
            build-system = [ py.hatchling ];
            pythonRelaxDeps = true;
            dependencies = [ evalCorePkg ] ++ skillsRuntimeDeps;
            doCheck = false;
            pythonImportsCheck = [
              "artagon_eval_skills"
              "artagon_eval_skills.spec_adapter"
              "artagon_eval_skills.cli.app"
              "artagon_eval_skills.cli.lint"
            ];
          };

          umbrellaPkg = py.toPythonModule (py.buildPythonApplication {
            pname = "artagon-skills-eval";
            version = "0.2.0";
            pyproject = true;
            src = umbrellaSrc;
            build-system = [ py.hatchling ];
            pythonRelaxDeps = true;
            dependencies = [
              evalCorePkg
              evalSkillsPkg
            ];
            doCheck = false;
            pythonImportsCheck = [
              "artagon_skills_eval"
              "artagon_eval_core"
              "artagon_eval_skills"
            ];
          });

          evalSkilloptPkg = py.buildPythonPackage {
            pname = "artagon-eval-skillopt";
            version = "0.2.0";
            pyproject = true;
            src = skilloptAdapterSrc;
            build-system = [ py.hatchling ];
            pythonRelaxDeps = true;
            dependencies = [
              evalCorePkg
              evalSkillsPkg
              py.markdown-it-py
              skilloptUpstreamPkg
            ];
            doCheck = false;
            pythonImportsCheck = [ "artagon_eval_skillopt" ];
          };

          # -----------------------------------------------------------------
          # 4. Python Environments & System Runtime Toolchains
          # -----------------------------------------------------------------
          evalPythonEnv = python.withPackages (ps: allCoreRuntimeDeps ++ [
            evalCorePkg
            evalSkillsPkg
            umbrellaPkg
            ps.hatchling
            ps.hypothesis
            ps.pytest
          ]);

          devPythonEnv = python.withPackages (ps: allCoreRuntimeDeps ++ [
            evalCorePkg
            evalSkillsPkg
            umbrellaPkg
            ps.hatchling
            ps.hypothesis
            ps.pytest
            ps.pytest-cov
            ps.pytest-xdist
            ps.radon
            ps.types-protobuf
            ps.types-pyyaml
          ]);

          skilloptPythonEnv = python.withPackages (ps: allCoreRuntimeDeps ++ [
            evalCorePkg
            evalSkillsPkg
            umbrellaPkg
            evalSkilloptPkg
            skilloptUpstreamPkg
            ps.markdown-it-py
            ps.setuptools
            ps.wheel
            ps.hypothesis
            ps.pytest
          ]);

          baseSystemTools = [
            pkgs.bash
            pkgs.coreutils
            pkgs.git
            pkgs.jq
            pkgs.ripgrep
            pkgs.tmux
          ];

          runtimeTools = [ evalPythonEnv ] ++ baseSystemTools;

          devTools = [
            devPythonEnv
            pkgs.ast-grep
            pkgs.basedpyright
            pkgs.mypy
            pkgs.ruff
            pkgs.uv
          ] ++ baseSystemTools;

          skilloptRuntimeTools = [ skilloptPythonEnv ] ++ baseSystemTools;

          # -----------------------------------------------------------------
          # 5. Locked-Versions Receipt Parity (packages + tools)
          # -----------------------------------------------------------------
          actualVersionsJson = builtins.toJSON {
            nixpkgs_rev = flakeLock.nodes.nixpkgs.locked.rev;
            nixpkgs_narHash = flakeLock.nodes.nixpkgs.locked.narHash;
            python = python.version;
            packages = {
              click = py.click.version;
              "detect-secrets" = py.detect-secrets.version;
              duckdb = py.duckdb.version;
              expression = expressionPkg.version;
              hatchling = py.hatchling.version;
              hypothesis = py.hypothesis.version;
              jinja2 = py.jinja2.version;
              jmespath = py.jmespath.version;
              jsonschema = py.jsonschema.version;
              msgspec = py.msgspec.version;
              "opentelemetry-proto" = py.opentelemetry-proto.version;
              packaging = py.packaging.version;
              pluggy = py.pluggy.version;
              protobuf = py.protobuf.version;
              pyarrow = py.pyarrow.version;
              pydantic = py.pydantic.version;
              "pydantic-settings" = py.pydantic-settings.version;
              pytest = py.pytest.version;
              pyyaml = py.pyyaml.version;
              rfc8785 = py.rfc8785.version;
              "rpds-py" = py.rpds-py.version;
              "skills-ref" = skillsRefPkg.version;
              strictyaml = py.strictyaml.version;
              structlog = py.structlog.version;
              tomlkit = py.tomlkit.version;
              typer = py.typer.version;
              "typing-extensions" = py.typing-extensions.version;
            };
            tools = {
              "ast-grep" = pkgs.ast-grep.version;
              basedpyright = pkgs.basedpyright.version;
              mypy = pkgs.mypy.version;
              radon = py.radon.version;
              ruff = pkgs.ruff.version;
              uv = pkgs.uv.version;
            };
          };

          # -----------------------------------------------------------------
          # 6. Wrapped CLI Binaries (Nix store PATH pinned, runtime HOME inherited)
          # -----------------------------------------------------------------
          mkWrappedBin = binName: binPkg: tools: pkgs.writeTextFile {
            name = binName;
            destination = "/bin/${binName}";
            executable = true;
            text = ''
              #!${pkgs.runtimeShell}
              set -eu
              export PYTHONNOUSERSITE=1
              export PYTHONDONTWRITEBYTECODE=1
              export HARNESS_EVAL_REQUIRE_NIX_DEPS=1
              export PATH="${pkgs.lib.makeBinPath tools}:$PATH"
              exec ${binPkg}/bin/${binName} "$@"
            '';
          };

          harnessEvalApp = mkWrappedBin "harness-eval" umbrellaPkg runtimeTools;
          skillEvalApp = mkWrappedBin "skill-eval" umbrellaPkg runtimeTools;
          skillLintApp = mkWrappedBin "skill-lint" umbrellaPkg runtimeTools;
          nixCheckApp = mkWrappedBin "harness-eval-nix-check" umbrellaPkg runtimeTools;
          skilloptRunnerApp = mkWrappedBin "skillopt-runner" umbrellaPkg skilloptRuntimeTools;

          unifiedDefaultPkg = pkgs.symlinkJoin {
            name = "artagon-skills-eval-0.2.0";
            paths = [
              harnessEvalApp
              skillEvalApp
              skillLintApp
              nixCheckApp
            ];
            passthru = {
              pythonModule = umbrellaPkg;
              coreModule = evalCorePkg;
              skillsModule = evalSkillsPkg;
              pythonEnv = evalPythonEnv;
            };
          };

          # -----------------------------------------------------------------
          # 7. Isolated Eval Execution Shell Hook
          # -----------------------------------------------------------------
          scrubMeteredCmd = builtins.concatStringsSep "\n" (
            map (v: "unset ${v}") meteredEnvVars
          );

          evalShellHook = ''
            export PYTHONDONTWRITEBYTECODE=1
            export PYTHONNOUSERSITE=1
            export PYTHONSAFEPATH=1
            export HARNESS_EVAL_REQUIRE_NIX_DEPS=1
            export HARNESS_EVAL_NIX_SHELL=1

            # Scrub ambient metered API keys / BYOK toggles inherited from host RC files
            ${scrubMeteredCmd}
            for _var in $(compgen -e); do
              case "$_var" in
                ANTHROPIC_BEDROCK_*|ANTHROPIC_VERTEX_*|COPILOT_PROVIDER_*)
                  unset "$_var"
                  ;;
              esac
            done
            unset _var

            printf '[artagon-skills-eval nix-shell] python=%s (isolated, metered env scrubbed)\n' \
              "$(python --version 2>&1)" >&2
          '';

          # -----------------------------------------------------------------
          # 8. Pure Offline Verification Check (Zero Network, Empty $HOME)
          # -----------------------------------------------------------------
          offlineCheck =
            assert _assertCleanSource;
            assert lockedReceipt.nixpkgs_rev == flakeLock.nodes.nixpkgs.locked.rev
              || builtins.throw "nix/locked-versions.json nixpkgs_rev does not match flake.lock";
            assert lockedReceipt.nixpkgs_narHash == flakeLock.nodes.nixpkgs.locked.narHash
              || builtins.throw "nix/locked-versions.json nixpkgs_narHash does not match flake.lock";
            pkgs.runCommand "artagon-skills-eval-offline-check" {
              nativeBuildInputs = runtimeTools;
              passAsFile = [ "actualVersionsJson" ];
              inherit actualVersionsJson;
            } ''
              set -euo pipefail
              export PYTHONDONTWRITEBYTECODE=1
              export PYTHONNOUSERSITE=1
              export CI=1
              export HYPOTHESIS_PROFILE=ci
              export HOME="$TMPDIR/home"
              mkdir -p "$HOME"
              cp -R ${offlineTestSrc} source
              chmod -R u+w source
              cd source
              export HARNESS_EVAL_REQUIRE_NIX_DEPS=1
              export PYTHONPATH="${evalCorePkg}/${python.sitePackages}:${evalSkillsPkg}/${python.sitePackages}:${umbrellaPkg}/${python.sitePackages}''${PYTHONPATH:+:$PYTHONPATH}"

              test -d "${evalCorePkg}/${python.sitePackages}/artagon_eval_core"
              test -d "${evalSkillsPkg}/${python.sitePackages}/artagon_eval_skills"

              python - "$actualVersionsJsonPath" nix/locked-versions.json <<'PY'
              import json, sys
              actual = json.load(open(sys.argv[1], encoding="utf-8"))
              committed = json.load(open(sys.argv[2], encoding="utf-8"))
              for key in ("nixpkgs_rev", "nixpkgs_narHash", "python", "packages", "tools"):
                  assert committed[key] == actual[key], (key, committed[key], actual[key])
              PY

              python -m pytest -q -p no:cacheprovider --import-mode=importlib \
                packages/artagon-eval-core/tests \
                packages/artagon-eval-skills/tests

              touch "$out"
            '';
        in {
          devShells = {
            default = pkgs.mkShell {
              name = "artagon-skills-eval-shell";
              packages = runtimeTools ++ [ harnessEvalApp skillEvalApp skillLintApp nixCheckApp ];
              shellHook = evalShellHook;
            };
            dev = pkgs.mkShell {
              name = "artagon-skills-eval-dev-shell";
              packages = devTools ++ [ harnessEvalApp skillEvalApp skillLintApp nixCheckApp ];
              shellHook = evalShellHook + ''
                printf '[artagon-skills-eval nix-shell:dev] ruff=%s mypy=%s basedpyright=%s uv=%s\n' \
                  "$(ruff --version)" "$(mypy --version)" "$(basedpyright --version)" "$(uv --version)" >&2
              '';
            };
            skillopt = pkgs.mkShell {
              name = "artagon-skills-eval-skillopt-shell";
              packages = skilloptRuntimeTools ++ [ harnessEvalApp skillEvalApp skillLintApp skilloptRunnerApp ];
              shellHook = evalShellHook + ''
                printf '[artagon-skills-eval nix-shell:skillopt] skillopt=0.2.0 (pinned)\n' >&2
              '';
            };
          };

          checks = {
            offline = offlineCheck;
          };

          packages = {
            default = unifiedDefaultPkg;
            artagon-skills-eval = umbrellaPkg;
            artagon-eval-core = evalCorePkg;
            artagon-eval-skills = evalSkillsPkg;
            harness-eval = harnessEvalApp;
            skill-eval = skillEvalApp;
            skill-lint = skillLintApp;
            harness-eval-nix-check = nixCheckApp;
            skillopt = evalSkilloptPkg;
            skillopt-runner = skilloptRunnerApp;
          };

          apps = {
            default = { type = "app"; program = "${harnessEvalApp}/bin/harness-eval"; };
            harness-eval = { type = "app"; program = "${harnessEvalApp}/bin/harness-eval"; };
            skill-eval = { type = "app"; program = "${skillEvalApp}/bin/skill-eval"; };
            skill-lint = { type = "app"; program = "${skillLintApp}/bin/skill-lint"; };
            harness-eval-nix-check = { type = "app"; program = "${nixCheckApp}/bin/harness-eval-nix-check"; };
            skillopt-runner = { type = "app"; program = "${skilloptRunnerApp}/bin/skillopt-runner"; };
          };
        };
    in
    assert _assertCleanSource; {
      devShells = forAllSystems (system: (perSystem system).devShells);
      checks = forAllSystems (system: (perSystem system).checks);
      packages = forAllSystems (system: (perSystem system).packages);
      apps = forAllSystems (system: (perSystem system).apps);
    };
}
