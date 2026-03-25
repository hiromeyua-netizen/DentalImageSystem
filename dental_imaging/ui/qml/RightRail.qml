import QtQuick
import QtQuick.Layouts
import "components"

// Right vertical tool rail — icon-only SVG buttons, matching Occuscope reference.
Rectangle {
    id: root
    color: Qt.rgba(0.08, 0.09, 0.11, 0.72)

    // Left border separator
    Rectangle {
        anchors { left: parent.left; top: parent.top; bottom: parent.bottom }
        width: 1
        color: Qt.rgba(1, 1, 1, 0.09)
    }

    ColumnLayout {
        anchors { fill: parent; topMargin: 14; bottomMargin: 14; leftMargin: 8; rightMargin: 8 }
        spacing: 4

        // ── Flip pair ────────────────────────────────────────────────────
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 4

            RailButton {
                iconSource: Qt.resolvedUrl("icons/flip_v.svg")
                tooltip:    "Flip vertical"
                implicitWidth: 44; implicitHeight: 40
                onClicked:  bridge.onFlipV()
            }
            RailButton {
                iconSource: Qt.resolvedUrl("icons/flip_h.svg")
                tooltip:    "Flip horizontal"
                implicitWidth: 44; implicitHeight: 40
                onClicked:  bridge.onFlipH()
            }
        }

        // ── Rotate pair ──────────────────────────────────────────────────
        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            spacing: 4

            RailButton {
                iconSource: Qt.resolvedUrl("icons/rotate_cw.svg")
                tooltip:    "Rotate clockwise"
                implicitWidth: 44; implicitHeight: 40
                onClicked:  bridge.onRotateCw()
            }
            RailButton {
                iconSource: Qt.resolvedUrl("icons/rotate_ccw.svg")
                tooltip:    "Rotate counter-clockwise"
                implicitWidth: 44; implicitHeight: 40
                onClicked:  bridge.onRotateCcw()
            }
        }

        // ── Separator ────────────────────────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(1,1,1,0.08); Layout.topMargin: 4; Layout.bottomMargin: 4 }

        // ── Image settings ───────────────────────────────────────────────
        RailButton {
            id:          imgSettingsBtn
            Layout.alignment: Qt.AlignHCenter
            iconSource:  Qt.resolvedUrl("icons/image_settings.svg")
            tooltip:     "Image settings"
            isChecked:   bridge.imageSettingsVisible
            onClicked:   bridge.onImageSettingsToggled(!bridge.imageSettingsVisible)
        }

        // ── Settings ─────────────────────────────────────────────────────
        RailButton {
            Layout.alignment: Qt.AlignHCenter
            iconSource:  Qt.resolvedUrl("icons/settings.svg")
            tooltip:     "Settings"
            isChecked:   bridge.settingsPanelVisible
            onClicked:   bridge.onSettingsPanelToggled(!bridge.settingsPanelVisible)
        }

        // ── Capture ──────────────────────────────────────────────────────
        RailButton {
            Layout.alignment: Qt.AlignHCenter
            iconSource:  Qt.resolvedUrl("icons/camera.svg")
            tooltip:     "Capture full-resolution image"
            enabled:     bridge.capturable
            opacity:     bridge.capturable ? 1.0 : 0.38
            onClicked:   bridge.onCapture()
        }

        // ── Separator ────────────────────────────────────────────────────
        Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(1,1,1,0.08); Layout.topMargin: 4; Layout.bottomMargin: 4 }

        // ── Auto colour ──────────────────────────────────────────────────
        RailButton {
            Layout.alignment: Qt.AlignHCenter
            iconSource:   Qt.resolvedUrl("icons/color_balance.svg")
            tooltip:      "Auto colour balance"
            isChecked:    bridge.autoColor
            // Green tint when active
            activeColor:  bridge.autoColor ? Qt.rgba(0.30, 0.65, 0.38, 0.50) : Qt.rgba(1,1,1,0.18)
            checkedBorder: bridge.autoColor ? Qt.rgba(0.55, 0.88, 0.62, 0.65) : Qt.rgba(1,1,1,0.35)
            onClicked:    bridge.onAutoColorToggled(!bridge.autoColor)
        }

        // ── Recenter ROI ─────────────────────────────────────────────────
        RailButton {
            Layout.alignment: Qt.AlignHCenter
            iconSource: Qt.resolvedUrl("icons/crosshair.svg")
            tooltip:    "Recenter ROI"
            onClicked:  bridge.onRecenterRoi()
        }

        // ── ROI mode ─────────────────────────────────────────────────────
        RailButton {
            Layout.alignment: Qt.AlignHCenter
            iconSource:   Qt.resolvedUrl("icons/roi.svg")
            tooltip:      "ROI mode"
            isChecked:    bridge.roiMode
            // Blue tint when active
            activeColor:  bridge.roiMode ? Qt.rgba(0.28, 0.50, 0.90, 0.44) : Qt.rgba(1,1,1,0.18)
            checkedBorder: bridge.roiMode ? Qt.rgba(0.50, 0.72, 1.0, 0.60) : Qt.rgba(1,1,1,0.35)
            onClicked:    bridge.onRoiModeToggled(!bridge.roiMode)
        }

        Item { Layout.fillHeight: true }
    }
}
