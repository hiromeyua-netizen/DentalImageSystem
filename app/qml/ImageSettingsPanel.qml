import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import "components"

// Floating Image Settings — frosted panel; labels above sliders; inverted track (ref UI).
Rectangle {
    id: panel
    readonly property bool compact: (Window.window ? Window.window.height : 720) < 760
                                    || (Window.window ? Window.window.width : 1280) < 1080

    visible:      bridge.imageSettingsVisible
    width: {
        const w = Window.window ? Window.window.width : 1280
        return compact ? Math.min(306, Math.max(236, w - 56))
                       : Math.min(324, Math.max(248, w - 48))
    }
    readonly property real contentTop: hdr.height + 10 + sep.height + 12
    readonly property real contentBottomPadding: compact ? 12 : 14
    readonly property real maxRowsVisibleH: compact ? 360 : 430
    readonly property real rowsViewportH: Math.min(rows.implicitHeight, maxRowsVisibleH)
    height:       contentTop + rowsViewportH + contentBottomPadding
    radius:       14
    // Glass-style: more transparent so the camera preview reads through (ref)
    color:        Qt.rgba(0.11, 0.10, 0.12, 0.58)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.22)
    z: 100

    opacity: visible ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
    scale:   visible ? 1.0 : 0.96
    Behavior on scale   { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }

    // ── Header ────────────────────────────────────────────────────────────
    RowLayout {
        id: hdr
        anchors { top: parent.top; left: parent.left; right: parent.right; topMargin: compact ? 14 : 16; leftMargin: compact ? 14 : 16; rightMargin: 12 }
        spacing: 8

        Text {
            text: "Image Settings"
            font.pixelSize: compact ? 16 : 17
            font.bold: true
            color: "#ffffff"
            Layout.alignment: Qt.AlignVCenter
        }

        Item {
            Layout.fillWidth: true
            Layout.minimumHeight: 36
            MouseArea {
                anchors.fill: parent
                drag.target: panel
                drag.axis: Drag.XAndYAxis
                cursorShape: Qt.SizeAllCursor
            }
        }

        Text {
            id: rstLbl
            text: "Reset"
            font.pixelSize: 14
            font.weight: Font.Normal
            color: Qt.rgba(1, 1, 1, 0.82)
            Layout.alignment: Qt.AlignVCenter
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                hoverEnabled: true
                onEntered: rstLbl.color = Qt.rgba(1, 1, 1, 1)
                onExited:  rstLbl.color = Qt.rgba(1, 1, 1, 0.82)
                onClicked: bridge.onImageSettingsReset()
            }
        }

        Text {
            id: clsLbl
            text: "✕"
            font.pixelSize: 17
            color: Qt.rgba(1, 1, 1, 0.78)
            leftPadding: 4
            rightPadding: 4
            Layout.alignment: Qt.AlignVCenter
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                hoverEnabled: true
                onEntered: clsLbl.color = Qt.rgba(1, 1, 1, 1)
                onExited:  clsLbl.color = Qt.rgba(1, 1, 1, 0.78)
                onClicked: bridge.onImageSettingsToggled(false)
            }
        }
    }

    Rectangle {
        id: sep
        anchors { left: parent.left; right: parent.right; top: hdr.bottom; leftMargin: compact ? 14 : 16; rightMargin: compact ? 14 : 16; topMargin: 10 }
        height: 1
        color: Qt.rgba(1, 1, 1, 0.12)
    }

    Flickable {
        id: rowsView
        anchors {
            top: sep.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
            topMargin: compact ? 12 : 14
            leftMargin: compact ? 14 : 16
            rightMargin: compact ? 14 : 16
            bottomMargin: compact ? 10 : 12
        }
        clip: true
        interactive: contentHeight > height
        contentHeight: rows.implicitHeight

        ColumnLayout {
            id: rows
            width: rowsView.width
            spacing: compact ? 12 : 14

            SettingRow { label: "Exposure";      value: bridge.exposure;      onMoved: (v) => bridge.onExposureChanged(v) }
            SettingRow { label: "Gain";          value: bridge.gain;          onMoved: (v) => bridge.onGainChanged(v) }
            SettingRow { label: "White Balance"; value: bridge.whiteBalance;  onMoved: (v) => bridge.onWhiteBalanceChanged(v) }
            SettingRow { label: "Contrast";      value: bridge.contrast;      onMoved: (v) => bridge.onContrastChanged(v) }
            SettingRow { label: "Saturation";    value: bridge.saturation;    onMoved: (v) => bridge.onSaturationChanged(v) }
            SettingRow { label: "Warmth";        value: bridge.warmth;        onMoved: (v) => bridge.onWarmthChanged(v) }
            SettingRow { label: "Tint";          value: bridge.tint;          onMoved: (v) => bridge.onTintChanged(v) }
        }
    }
}
