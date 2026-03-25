import QtQuick
import QtQuick.Layouts
import QtQuick.Controls
import QtQuick.Window
import "components"

// Settings modal — layout matches reference (Display / Capture / Storage / About).
Rectangle {
    id: panel

    visible: bridge.settingsPanelVisible
    width: {
        const w = Window.window ? Window.window.width : 1280
        return Math.min(400, Math.max(280, w - 40))
    }
    z:       100

    // When not set from outside, allow full growth (e.g. tests)
    property real maxPanelHeight: 10000

    // Header chrome: top padding + hdr + gap to sep + sep + gap above flick
    readonly property real _chromeTop: 18 + hdr.implicitHeight + 12 + 1 + 14
    readonly property real _chromeBottom: 16
    readonly property real _flickH: Math.min(
        body.implicitHeight,
        Math.max(0, maxPanelHeight - _chromeTop - _chromeBottom)
    )

    height: _chromeTop + _flickH + _chromeBottom

    radius:       20
    // Glassmorphism: lighter frosted panel so the preview shows through (ref image 2)
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
            id: settingsTitle
            text: "Settings"
            font.pixelSize: 17
            font.bold: true
            color: "#ffffff"
            Layout.alignment: Qt.AlignVCenter
            MouseArea {
                anchors.fill: parent
                drag.target: panel
                drag.axis: Drag.XAndYAxis
                cursorShape: Qt.SizeAllCursor
            }
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
            id: clsLbl
            text: "✕"
            font.pixelSize: 17
            color: Qt.rgba(1, 1, 1, 0.78)
            Layout.alignment: Qt.AlignVCenter
            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                hoverEnabled: true
                onEntered: clsLbl.color = "#ffffff"
                onExited:  clsLbl.color = Qt.rgba(1, 1, 1, 0.78)
                onClicked: bridge.onSettingsPanelToggled(false)
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
        id: flick
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
        contentHeight: body.implicitHeight
        flickableDirection: Flickable.VerticalFlick

        ColumnLayout {
            id: body
            width: flick.width
            spacing: 0

            // —— Display ——
            Text {
                text: "Display"
                font.pixelSize: 12
                font.weight: Font.Medium
                color: Qt.rgba(1, 1, 1, 0.62)
                Layout.bottomMargin: 10
            }
            SettingsToggleRow {
                label: "Show Grid Overlay"
                active: bridge.showGridOverlay
                onToggled: (v) => bridge.onShowGridOverlayToggled(v)
                Layout.bottomMargin: 14
            }
            SettingsToggleRow {
                label: "Show Crosshair"
                active: bridge.showCrosshair
                onToggled: (v) => bridge.onShowCrosshairToggled(v)
                Layout.bottomMargin: 14
            }
            SettingsToggleRow {
                label: "Auto Scale Preview"
                active: bridge.autoScalePreview
                onToggled: (v) => bridge.onAutoScalePreviewToggled(v)
                Layout.bottomMargin: 22
            }

            // —— Capture ——
            Text {
                text: "Capture"
                font.pixelSize: 12
                font.weight: Font.Medium
                color: Qt.rgba(1, 1, 1, 0.62)
                Layout.bottomMargin: 10
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: 12
                Text {
                    text: "PREVIEW"
                    font.pixelSize: 11
                    font.weight: Font.Medium
                    color: Qt.rgba(1, 1, 1, 0.52)
                }
                Item { Layout.fillWidth: true }
                Text {
                    id: expAll
                    text: "Export All"
                    font.pixelSize: 12
                    color: Qt.rgba(1, 1, 1, 0.82)
                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: bridge.onExportAllClicked()
                    }
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Layout.bottomMargin: 14
                SettingsPillButton {
                    text: "JPG"
                    active: !bridge.captureFormatPng
                    onClicked: bridge.onCaptureFormatPng(false)
                }
                SettingsPillButton {
                    text: "PNG"
                    active: bridge.captureFormatPng
                    onClicked: bridge.onCaptureFormatPng(true)
                }
                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.bottomMargin: 14
                Text {
                    text: "Image Quality"
                    font.pixelSize: 13
                    color: Qt.rgba(1, 1, 1, 0.9)
                    Layout.fillWidth: true
                }
                Text {
                    text: bridge.imageQuality + "%"
                    font.pixelSize: 13
                    font.bold: true
                    color: "#ffffff"
                }
            }

            Text {
                text: "LEDs Preset"
                font.pixelSize: 13
                color: Qt.rgba(1, 1, 1, 0.88)
                Layout.bottomMargin: 8
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Layout.bottomMargin: 16
                SettingsPillButton {
                    text: "50%"
                    active: !bridge.ledsPresetAuto
                    onClicked: bridge.onLedsPresetAuto(false)
                }
                SettingsPillButton {
                    text: "AUTO"
                    active: bridge.ledsPresetAuto
                    onClicked: bridge.onLedsPresetAuto(true)
                }
                Item { Layout.fillWidth: true }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Layout.bottomMargin: 16
                SettingsPillButton {
                    text: "SNAPSHOT"
                    Layout.fillWidth: true
                    active: !bridge.captureBurstMode
                    onClicked: bridge.onCaptureBurstMode(false)
                }
                SettingsPillButton {
                    text: "BURST"
                    Layout.fillWidth: true
                    active: bridge.captureBurstMode
                    onClicked: bridge.onCaptureBurstMode(true)
                }
            }

            Text {
                text: "Delay"
                font.pixelSize: 12
                color: Qt.rgba(1, 1, 1, 0.75)
                Layout.bottomMargin: 8
            }

            Row {
                Layout.fillWidth: true
                Layout.preferredHeight: 42
                spacing: 8
                Layout.bottomMargin: 16

                Repeater {
                    model: [2, 5, 10, 15, 30, 60]
                    delegate: Rectangle {
                        required property int modelData
                        readonly property bool sel: bridge.captureDelaySec === modelData
                        width: 40
                        height: 40
                        radius: 20
                        // Selected: solid white disc + dark label (ref image 2)
                        color: sel ? "#f2f2f6" : "transparent"
                        border.width: 1
                        border.color: sel ? Qt.rgba(1, 1, 1, 0.65) : Qt.rgba(1, 1, 1, 0.45)

                        Text {
                            anchors.centerIn: parent
                            text: modelData
                            font.pixelSize: 12
                            font.bold: sel
                            color: sel ? "#1a1c22" : "#ffffff"
                        }
                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: bridge.onCaptureDelaySec(modelData)
                        }
                    }
                }
            }

            SettingsToggleRow {
                label: "Camera Sound"
                active: bridge.cameraSoundEnabled
                onToggled: (v) => bridge.onCameraSoundToggled(v)
                Layout.bottomMargin: 22
            }

            // —— Storage ——
            Text {
                text: "Storage"
                font.pixelSize: 12
                font.weight: Font.Medium
                color: Qt.rgba(1, 1, 1, 0.62)
                Layout.bottomMargin: 10
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 10
                Layout.bottomMargin: 22
                SettingsPillButton {
                    text: "SYSTEM"
                    Layout.fillWidth: true
                    active: !bridge.storageSdcard
                    onClicked: bridge.onStorageSdcard(false)
                }
                SettingsPillButton {
                    text: "SD CARD"
                    Layout.fillWidth: true
                    active: bridge.storageSdcard
                    onClicked: bridge.onStorageSdcard(true)
                }
            }

            // —— About ——
            Text {
                text: "About"
                font.pixelSize: 12
                font.weight: Font.Medium
                color: Qt.rgba(1, 1, 1, 0.62)
                Layout.bottomMargin: 8
            }
            Text {
                Layout.fillWidth: true
                horizontalAlignment: Text.AlignHCenter
                text: "OccuView ALPHA V1.0  ©2026"
                font.pixelSize: 11
                color: Qt.rgba(1, 1, 1, 0.58)
                wrapMode: Text.WordWrap
            }
        }
    }
}
