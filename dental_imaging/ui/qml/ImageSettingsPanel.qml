import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

// Floating image-settings panel (exposure, gain, white balance, etc.)
Rectangle {
    id: root
    visible:      bridge.imageSettingsVisible
    width:        320
    height:       col.implicitHeight + 32
    radius:       14
    color:        Qt.rgba(0.10, 0.11, 0.14, 0.90)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.12)

    // Appear / disappear animation
    opacity:   visible ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }
    scale:     visible ? 1.0 : 0.95
    Behavior on scale   { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } }

    layer.enabled: true   // enables clean border rendering

    // ── Header ────────────────────────────────────────────────────────────
    RowLayout {
        id:    header
        anchors { top: parent.top; left: parent.left; right: parent.right; margins: 16 }
        height: 40

        Text {
            text:           "Image Settings"
            font.pixelSize: 15
            font.bold:      true
            color:          "#f0f0f4"
        }
        Item { Layout.fillWidth: true }
        // Reset button
        Text {
            text:           "Reset"
            font.pixelSize: 12
            color:          "#8888a0"
            MouseArea {
                anchors.fill: parent
                cursorShape:  Qt.PointingHandCursor
                hoverEnabled: true
                onEntered:    parent.color = "#c0c0d0"
                onExited:     parent.color = "#8888a0"
                onClicked:    bridge.onImageSettingsReset()
            }
        }
        // Close button
        Text {
            text:           "✕"
            font.pixelSize: 14
            color:          "#8888a0"
            leftPadding:    8
            MouseArea {
                anchors.fill: parent
                cursorShape:  Qt.PointingHandCursor
                hoverEnabled: true
                onEntered:    parent.color = "#ffffff"
                onExited:     parent.color = "#8888a0"
                onClicked:    bridge.onImageSettingsToggled(false)
            }
        }
    }

    // Divider
    Rectangle {
        anchors { left: parent.left; right: parent.right; top: header.bottom }
        anchors.leftMargin: 16; anchors.rightMargin: 16
        height: 1; color: Qt.rgba(1,1,1,0.10)
    }

    // ── Sliders ───────────────────────────────────────────────────────────
    ColumnLayout {
        id:  col
        anchors { top: header.bottom; left: parent.left; right: parent.right; topMargin: 12; leftMargin: 16; rightMargin: 16 }
        spacing: 12

        SettingRow { label: "Exposure";     value: bridge.exposure;     onMoved: (v) => bridge.onExposureChanged(v) }
        SettingRow { label: "Gain";         value: bridge.gain;         onMoved: (v) => bridge.onGainChanged(v) }
        SettingRow { label: "White Balance"; value: bridge.whiteBalance; onMoved: (v) => bridge.onWhiteBalanceChanged(v) }
        SettingRow { label: "Contrast";     value: bridge.contrast;     onMoved: (v) => bridge.onContrastChanged(v) }
        SettingRow { label: "Saturation";   value: bridge.saturation;   onMoved: (v) => bridge.onSaturationChanged(v) }
        SettingRow { label: "Warmth";       value: bridge.warmth;       onMoved: (v) => bridge.onWarmthChanged(v) }
        SettingRow { label: "Tint";         value: bridge.tint;         onMoved: (v) => bridge.onTintChanged(v) }

        Item { height: 4 }
    }
}

// Inline slider row component
component SettingRow: RowLayout {
    property string label
    property int    value: 50
    signal moved(int v)

    spacing: 10
    Layout.fillWidth: true

    Text {
        text:           label
        font.pixelSize: 11
        color:          "#b0b0be"
        Layout.preferredWidth: 100
    }

    Slider {
        id:   sl
        Layout.fillWidth: true
        from: 0; to: 100
        value: parent.value
        stepSize: 1

        background: Rectangle {
            x: sl.leftPadding; y: sl.topPadding + (sl.availableHeight - height) / 2
            width: sl.availableWidth; height: 4; radius: 2
            color: Qt.rgba(1, 1, 1, 0.15)
            Rectangle {
                width: sl.visualPosition * parent.width
                height: parent.height; radius: 2
                color: Qt.rgba(1, 1, 1, 0.55)
            }
        }

        handle: Rectangle {
            x: sl.leftPadding + sl.visualPosition * (sl.availableWidth - width)
            y: sl.topPadding  + (sl.availableHeight - height) / 2
            width: 18; height: 18; radius: 9
            color: "white"
        }

        onMoved: parent.moved(Math.round(value))
    }

    Text {
        text:           sl.value.toFixed(0) + "%"
        font.pixelSize: 11
        color:          "#d0d0dc"
        Layout.preferredWidth: 36
        horizontalAlignment:   Text.AlignRight
    }
}
