# dotfiles と同様に、Nix profile を開発シェルとコンテナで共有する。
ARG NIX_VERSION=2.35.1
ARG NIX_IMAGE_DIGEST=sha256:377d4887aca98f0dfa12971c1ea6d6a625a435d8b610d4c95a436843da6fbfd1
FROM nixos/nix:${NIX_VERSION}@${NIX_IMAGE_DIGEST}

RUN mkdir -p /etc/nix \
  && printf '%s\n' \
  'experimental-features = nix-command flakes' \
  'sandbox = false' \
  'filter-syscalls = false' \
  'max-jobs = auto' \
  'flake-registry = ' \
  >> /etc/nix/nix.conf

ENV SABAACCESSORY_PROFILE=/nix/var/nix/profiles/sabaaccessory-dev
WORKDIR /workspace

COPY flake.nix flake.lock ./
COPY nix ./nix

RUN nix develop --profile "$SABAACCESSORY_PROFILE" --command true \
  && nix registry add nixpkgs \
  "path:$(nix eval --raw --impure --expr '(builtins.getFlake "/workspace").inputs.nixpkgs.outPath')" \
  && rm -rf /root/.cache/nix

COPY . .
RUN chmod +x scripts/*.sh .github/scripts/*.sh

ENTRYPOINT ["/bin/sh", "/workspace/scripts/docker-entrypoint.sh"]
CMD []
