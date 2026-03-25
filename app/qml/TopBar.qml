import QtQuick
import QtQuick.Layouts
import QtQuick.Window

// ── Top chrome bar — floating pill, glass-style (matches rail / bottom bar) ───
// Layout:  [Logo]  [spacer]  [stream stats]  [CONNECTED pill]  [Power button]
Rectangle {
    id: topBarRoot
    radius: height * 0.5
    clip: true
    color: Qt.rgba(0.06, 0.07, 0.11, 0.44)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.26)

    readonly property var win: Window.window
    readonly property real _aw: win ? win.width : 1280
    readonly property bool _compact: _aw < 1100
    readonly property bool _narrow: _aw < 820

    RowLayout {
        anchors {
            fill: parent
            leftMargin: topBarRoot._narrow ? 10 : (topBarRoot._compact ? 14 : 18)
            rightMargin: topBarRoot._narrow ? 10 : (topBarRoot._compact ? 14 : 18)
        }
        spacing: topBarRoot._narrow ? 8 : (topBarRoot._compact ? 12 : 18)

        // ── Brand ─────────────────────────────────────────────────────────
        Column {
            spacing: topBarRoot._compact ? 1 : 2
            Layout.alignment: Qt.AlignVCenter

            Text {
                text: "OCCUSCOPE"
                font {
                    pixelSize: topBarRoot._narrow ? 11 : (topBarRoot._compact ? 12 : 14)
                    bold: true
                    letterSpacing: topBarRoot._narrow ? 0.8 : 1.2
                }
                color: "#ffffff"
            }
            Text {
                visible: !topBarRoot._narrow
                text: "DIGITAL IMAGING SYSTEM"
                font { pixelSize: topBarRoot._compact ? 7 : 8; letterSpacing: 0.9 }
                color: "#7888a0"
            }
        }

        Item { Layout.fillWidth: true }

        // ── Stream statistics ──────────────────────────────────────────────
        Text {
            visible: topBarRoot._aw > 900
            text: bridge.statsText
            font {
                pixelSize: topBarRoot._compact ? 10 : 12
                weight: Font.Medium
                letterSpacing: 0.3
            }
            color: "#d8d8e6"
            Layout.alignment: Qt.AlignVCenter
            Layout.maximumWidth: topBarRoot._compact ? Math.min(220, topBarRoot._aw * 0.22) : 4096
            elide: Text.ElideRight
        }

        // ── CONNECTED pill (ref: solid white + dark label when live) ────────
        Rectangle {
            height: topBarRoot._compact ? 26 : 30
            width:  pillText.implicitWidth + (topBarRoot._compact ? 20 : 26)
            radius: height * 0.5
            color:        bridge.connected ? "#f2f2f6" : Qt.rgba(0.8, 0.2, 0.18, 0.22)
            border.width: 1
            border.color: bridge.connected ? Qt.rgba(1, 1, 1, 0.45) : Qt.rgba(1, 0.4, 0.38, 0.45)
            Layout.alignment: Qt.AlignVCenter

            Behavior on color        { ColorAnimation { duration: 280 } }
            Behavior on border.color { ColorAnimation { duration: 280 } }

            Text {
                id: pillText
                anchors.centerIn: parent
                text: bridge.connected ? "CONNECTED" : "DISCONNECTED"
                font {
                    pixelSize: topBarRoot._compact ? 8 : 10
                    bold: true
                    letterSpacing: topBarRoot._compact ? 0.5 : 0.8
                }
                color: bridge.connected ? "#1a1c22" : "#ff9090"
                Behavior on color { ColorAnimation { duration: 280 } }
            }
        }

        // ── Power button ───────────────────────────────────────────────────
        Rectangle {
            id: powerBtn
            width: topBarRoot._compact ? 36 : 42
            height: topBarRoot._compact ? 36 : 42
            radius: width * 0.5
            color: pwrMa.pressed       ? "#d0d0d8"
                 : pwrMa.containsMouse ? "#ffffff"
                 :                       Qt.rgba(1, 1, 1, 0.92)
            Layout.alignment: Qt.AlignVCenter
            Behavior on color { ColorAnimation { duration: 100 } }

            Image {
                anchors.centerIn: parent
                source:    Qt.resolvedUrl("icons/power.svg")
                sourceSize: Qt.size(topBarRoot._compact ? 18 : 20, topBarRoot._compact ? 18 : 20)
                fillMode:  Image.PreserveAspectFit
            }

            MouseArea {
                id: pwrMa; anchors.fill: parent
                hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                onClicked: bridge.onPowerClicked()
            }

            scale: pwrMa.pressed ? 0.90 : 1.0
            Behavior on scale { NumberAnimation { duration: 80 } }
        }
    }
}
