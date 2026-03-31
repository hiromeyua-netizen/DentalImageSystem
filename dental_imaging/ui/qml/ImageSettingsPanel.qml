import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import "components"

// Floating image-settings panel (exposure, gain, white balance, etc.)
Rectangle {
    id: root
    visible:      bridge.imageSettingsVisible
    width:        320
    height:       sliderCol.implicitHeight + 32
    radius:       14
    color:        Qt.rgba(0.10, 0.11, 0.14, 0.90)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.12)
    layer.enabled: true

    // Appear / disappear animation
    opacity: visible ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
    scale:   visible ? 1.0 : 0.95
    Behavior on scale   { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

    // ── Header ────────────────────────────────────────────────────────────
    RowLayout {
        id:     headerRow
        anchors { top: parent.top; left: parent.left; right: parent.right; margins: 16 }
        height: 40

        Text {
            text:           "Image Settings"
            font.pixelSize: 15
            font.bold:      true
            color:          "#f0f0f4"
        }

        Item { Layout.fillWidth: true }

        Text {
            id: resetLabel
            text:           "Reset"
            font.pixelSize: 12
            color:          "#8888a0"
            MouseArea {
                anchors.fill: parent
                cursorShape:  Qt.PointingHandCursor
                hoverEnabled: true
                onEntered:   resetLabel.color = "#c0c0d0"
                onExited:    resetLabel.color = "#8888a0"
                onClicked:   bridge.onImageSettingsReset()
            }
        }

        Text {
            id: closeLabel
            text:           "✕"
            font.pixelSize: 14
            color:          "#8888a0"
            leftPadding:    8
            MouseArea {
                anchors.fill: parent
                cursorShape:  Qt.PointingHandCursor
                hoverEnabled: true
                onEntered:   closeLabel.color = "#ffffff"
                onExited:    closeLabel.color = "#8888a0"
                onClicked:   bridge.onImageSettingsToggled(false)
            }
        }
    }

    // Header divider
    Rectangle {
        anchors { left: parent.left; right: parent.right; top: headerRow.bottom }
        anchors.leftMargin: 16; anchors.rightMargin: 16
        height: 1
        color:  Qt.rgba(1, 1, 1, 0.10)
    }

    // ── Sliders ───────────────────────────────────────────────────────────
    ColumnLayout {
        id: sliderCol
        anchors {
            top:         headerRow.bottom
            left:        parent.left
            right:       parent.right
            topMargin:   12
            leftMargin:  16
            rightMargin: 16
        }
        spacing: 12

        SettingRow { label: "Exposure";      value: bridge.exposure;      onMoved: (v) => bridge.onExposureChanged(v) }
        SettingRow { label: "Gain";          value: bridge.gain;          onMoved: (v) => bridge.onGainChanged(v) }
        SettingRow { label: "White Balance"; value: bridge.whiteBalance;  onMoved: (v) => bridge.onWhiteBalanceChanged(v) }
        SettingRow { label: "Contrast";      value: bridge.contrast;      onMoved: (v) => bridge.onContrastChanged(v) }
        SettingRow { label: "Saturation";    value: bridge.saturation;    onMoved: (v) => bridge.onSaturationChanged(v) }
        SettingRow { label: "Warmth";        value: bridge.warmth;        onMoved: (v) => bridge.onWarmthChanged(v) }
        SettingRow { label: "Tint";          value: bridge.tint;          onMoved: (v) => bridge.onTintChanged(v) }

        Item { height: 4 }
    }
}
