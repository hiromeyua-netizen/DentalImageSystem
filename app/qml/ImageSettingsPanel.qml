import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import "components"

// Floating Image Settings — frosted panel; labels above sliders; inverted track (ref UI).
Rectangle {
    id: panel

    visible:      bridge.imageSettingsVisible
    width: {
        const w = Window.window ? Window.window.width : 1280
        return Math.min(340, Math.max(280, w - 40))
    }
    z:       100
    property real maxPanelHeight: 10000

    // Match SettingsPanel shell pattern
    readonly property real _chromeTop: 18 + hdr.implicitHeight + 12 + 1 + 14
    readonly property real _chromeBottom: 16
    readonly property real _flickH: Math.min(
        rows.implicitHeight,
        Math.max(0, maxPanelHeight - _chromeTop - _chromeBottom)
    )

    height: _chromeTop + _flickH + _chromeBottom
    radius:       20
    // Match SettingsPanel glass background color.
    color:        Qt.rgba(0.06, 0.06, 0.08, 0.42)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.28)

    opacity: visible ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }
    scale:   visible ? 1.0 : 0.96
    Behavior on scale   { NumberAnimation { duration: 170; easing.type: Easing.OutCubic } }

    // ── Header ────────────────────────────────────────────────────────────
    RowLayout {
        id: hdr
        anchors { top: parent.top; left: parent.left; right: parent.right; topMargin: 18; leftMargin: 18; rightMargin: 14 }
        spacing: 10

        Text {
            text: "Image Settings"
            font.pixelSize: 17
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
        anchors { left: parent.left; right: parent.right; top: hdr.bottom; leftMargin: 18; rightMargin: 18; topMargin: 12 }
        height: 1
        color: Qt.rgba(1, 1, 1, 0.16)
    }

    Flickable {
        id: rowsView
        anchors {
            top: sep.bottom
            left: parent.left
            right: parent.right
            topMargin: 14
            leftMargin: 18
            rightMargin: 18
        }
        height: panel._flickH
        clip: true
        contentWidth: width
        contentHeight: rows.implicitHeight
        flickableDirection: Flickable.VerticalFlick

        ColumnLayout {
            id: rows
            width: rowsView.width
            spacing: 0

            SettingRow {
                label: "Exposure"
                value: bridge.exposure
                onMoved: (v) => bridge.onExposureChanged(v)
                Layout.bottomMargin: 3
            }
            SettingRow {
                label: "Gain"
                value: bridge.gain
                onMoved: (v) => bridge.onGainChanged(v)
                Layout.bottomMargin: 3
            }
            SettingRow {
                label: "White Balance"
                value: bridge.whiteBalance
                onMoved: (v) => bridge.onWhiteBalanceChanged(v)
                Layout.bottomMargin: 3
            }
            SettingRow {
                label: "Contrast"
                value: bridge.contrast
                onMoved: (v) => bridge.onContrastChanged(v)
                Layout.bottomMargin: 3
            }
            SettingRow {
                label: "Saturation"
                value: bridge.saturation
                onMoved: (v) => bridge.onSaturationChanged(v)
                Layout.bottomMargin: 3
            }
            SettingRow {
                label: "Warmth"
                value: bridge.warmth
                onMoved: (v) => bridge.onWarmthChanged(v)
                Layout.bottomMargin: 3
            }
            SettingRow {
                label: "Tint"
                value: bridge.tint
                onMoved: (v) => bridge.onTintChanged(v)
                Layout.bottomMargin: 3
            }
        }
    }
}
