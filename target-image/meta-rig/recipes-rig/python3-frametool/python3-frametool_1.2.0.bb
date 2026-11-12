SUMMARY = "frametool: COBS framing and CRC-16 for the telemetry link, with the C extension"
LICENSE = "CLOSED"

SRC_URI = "file://frametool-${PV}.tar.gz"
# Yocto 5.1 and later: S = "${UNPACKDIR}/frametool-${PV}"
S = "${WORKDIR}/frametool-${PV}"

# cmake passes the native python as Python_EXECUTABLE. python3targetconfig points that
# interpreter at the sysconfig data of the target, and the target's headers are named here.
inherit cmake python3targetconfig

EXTRA_OECMAKE += "-DPython_INCLUDE_DIR=${STAGING_INCDIR}/${PYTHON_DIR}${PYTHON_ABI}"

# The project's CMakeLists.txt writes _crc16*.so into src/frametool when it is not built as a wheel
do_install() {
    install -d ${D}${PYTHON_SITEPACKAGES_DIR}/frametool
    install -m 0644 ${S}/src/frametool/*.py ${S}/src/frametool/*.pyi ${S}/src/frametool/py.typed \
        ${D}${PYTHON_SITEPACKAGES_DIR}/frametool/
    install -m 0755 ${S}/src/frametool/_crc16*.so ${D}${PYTHON_SITEPACKAGES_DIR}/frametool/
}

FILES:${PN} += "${PYTHON_SITEPACKAGES_DIR}/frametool"
RDEPENDS:${PN} += "python3-core"
