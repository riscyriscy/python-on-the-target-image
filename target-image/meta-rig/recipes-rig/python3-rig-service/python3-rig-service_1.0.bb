SUMMARY = "Rig service: telemetry collector that reports to systemd"
LICENSE = "CLOSED"

SRC_URI = "file://rig-service-${PV}.tar.gz"
# Yocto 5.1 and later: S = "${UNPACKDIR}/rig-service-${PV}"
S = "${WORKDIR}/rig-service-${PV}"

inherit python_setuptools_build_meta systemd

# The standard library is split into packages. Name only the ones the service imports.
RDEPENDS:${PN} += "python3-core python3-io python3-frametool"

SYSTEMD_SERVICE:${PN} = "rig-service.service"
SYSTEMD_AUTO_ENABLE = "enable"

do_install:append() {
    install -d ${D}${systemd_system_unitdir}
    install -m 0644 ${S}/systemd/rig-service.service ${D}${systemd_system_unitdir}/
}
