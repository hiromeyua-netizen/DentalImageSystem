import QtQuick
import "components"

// Two stacked glass capsules (Occuscope ref): top = transform + settings; bottom = capture + tools.
Item {
    id: root
    implicitWidth: 76

    readonly property color _glass: Qt.rgba(0.06, 0.07, 0.11, 0.44)
    readonly property color _border: Qt.rgba(1, 1, 1, 0.26)
    // Inset icons from capsule ends and sides (ref: breathing room inside pill)
    readonly property real _padV: 16
    readonly property real _padH: 10

    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
        spacing: 12
        width: root.width

        // ── Top capsule: flip, rotate, image settings, app settings ───────
        Rectangle {
            width: root.width
            height: topCol.height + 2 * root._padV
            radius: width * 0.5
            clip: true
            color: _glass
            border.width: 1
            border.color: _border

            Column {
                id: topCol
                anchors.horizontalCenter: parent.horizontalCenter
                y: root._padV
                spacing: 6
                width: root.width - 2 * root._padH

                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/flip_v.svg")
                    tooltip: "Flip vertical"
                    onClicked: bridge.onFlipV()
                }
                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/flip_h.svg")
                    tooltip: "Flip horizontal"
                    onClicked: bridge.onFlipH()
                }
                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/rotate_cw.svg")
                    tooltip: "Rotate clockwise"
                    onClicked: bridge.onRotateCw()
                }
                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/rotate_ccw.svg")
                    tooltip: "Rotate counter-clockwise"
                    onClicked: bridge.onRotateCcw()
                }
                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/image_settings.svg")
                    tooltip: "Image settings"
                    isChecked: bridge.imageSettingsVisible
                    onClicked: bridge.onImageSettingsToggled(!bridge.imageSettingsVisible)
                }
                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/settings.svg")
                    tooltip: "Settings"
                    isChecked: bridge.settingsPanelVisible
                    onClicked: bridge.onSettingsPanelToggled(!bridge.settingsPanelVisible)
                }
            }
        }

        // ── Bottom capsule: capture, colour, crosshair, ROI ────────────────
        Rectangle {
            width: root.width
            height: botCol.height + 2 * root._padV
            radius: width * 0.5
            clip: true
            color: _glass
            border.width: 1
            border.color: _border

            Column {
                id: botCol
                anchors.horizontalCenter: parent.horizontalCenter
                y: root._padV
                spacing: 6
                width: root.width - 2 * root._padH

                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/camera.svg")
                    tooltip: "Capture  [Space]"
                    opacity: bridge.capturable ? 1.0 : 0.35
                    enabled: bridge.capturable
                    onClicked: bridge.onCapture()
                }
                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/color_balance.svg")
                    tooltip: "Auto colour balance"
                    isChecked: bridge.autoColor
                    activeColor: bridge.autoColor ? Qt.rgba(0.22, 0.70, 0.40, 0.35) : Qt.rgba(1, 1, 1, 0.14)
                    activeBorder: bridge.autoColor ? Qt.rgba(0.42, 0.88, 0.55, 0.60) : Qt.rgba(1, 1, 1, 0.36)
                    onClicked: bridge.onAutoColorToggled(!bridge.autoColor)
                }
                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/crosshair.svg")
                    tooltip: "Recenter ROI"
                    onClicked: bridge.onRecenterRoi()
                }
                RailButton {
                    width: parent.width
                    iconSource: Qt.resolvedUrl("icons/roi.svg")
                    tooltip: "ROI draw mode"
                    isChecked: bridge.roiMode
                    activeColor: bridge.roiMode ? Qt.rgba(0.22, 0.48, 0.95, 0.35) : Qt.rgba(1, 1, 1, 0.14)
                    activeBorder: bridge.roiMode ? Qt.rgba(0.42, 0.68, 1.00, 0.58) : Qt.rgba(1, 1, 1, 0.36)
                    onClicked: bridge.onRoiModeToggled(!bridge.roiMode)
                }
            }
        }
    }
}
