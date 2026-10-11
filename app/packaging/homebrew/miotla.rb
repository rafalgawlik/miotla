# Formuła Homebrew dla Miotły.
#
# Cel: repo tap `rafalgawlik/homebrew-tap`, plik `Formula/miotla.rb`.
# Instalacja:  brew install rafalgawlik/tap/miotla
#
# WAŻNE: po utworzeniu release'u vX.Y.Z na GitHubie podmień `sha256` pod `url`
# (użyj ./release-sha.sh X.Y.Z).
class Miotla < Formula
  include Language::Python::Virtualenv

  desc "macOS menu bar app for safe dev-Mac cleanup (shown in a window)"
  homepage "https://github.com/rafalgawlik/miotla"
  url "https://github.com/rafalgawlik/miotla/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "REPLACE_WITH_RELEASE_TARBALL_SHA256"
  license "MIT"

  depends_on :macos
  depends_on "python@3.12"

  resource "rumps" do
    url "https://files.pythonhosted.org/packages/b2/e2/2e6a47951290bd1a2831dcc50aec4b25d104c0cf00e8b7868cbd29cf3bfe/rumps-0.4.0.tar.gz"
    sha256 "17fb33c21b54b1e25db0d71d1d793dc19dc3c0b7d8c79dc6d833d0cffc8b1596"
  end

  resource "pyobjc-core" do
    url "https://files.pythonhosted.org/packages/a5/78/abc4ce5920305780aeb36b4067a86253378b36e29ba96673a3deb02eb03a/pyobjc_core-12.2.2.tar.gz"
    sha256 "3906452339cd06a3bb07df103c2511d4cb0f7a22d8771c0b802eba15d9a642b6"
  end

  resource "pyobjc-framework-Cocoa" do
    url "https://files.pythonhosted.org/packages/75/76/49c6da2c6a831020b4854ba20079d5a1030474bffc776b7b73c2eeff8c15/pyobjc_framework_cocoa-12.2.2.tar.gz"
    sha256 "c96c0ef69a71afbbb0e6a7d594b455c5fe47d62e0db376ee7a2b4b828c16ace9"
  end

  def install
    # Pakiet Pythona (apka) leży w podkatalogu app/; skrypt bin/miotla w repo.
    venv = virtualenv_create(libexec, "python3.12")
    venv.pip_install resources
    venv.pip_install_and_link buildpath/"app"
    # Skrypt sprzątający — część aplikacji (apka znajduje go na PATH).
    bin.install "bin/miotla"
  end

  # Włącza:  brew services start miotla
  service do
    run [opt_bin/"miotla-app"]
    keep_alive true
    log_path var/"log/miotla.log"
    error_log_path var/"log/miotla.log"
  end

  test do
    assert_match "miotla-app #{version}", shell_output("#{bin}/miotla-app --version")
    assert_match "Miotła", shell_output("#{bin}/miotla --help")
  end
end
