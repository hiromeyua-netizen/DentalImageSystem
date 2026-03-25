import QtQuick
import QtQuick.Layouts

// ── Top chrome bar — floating pill, glass-style (matches rail / bottom bar) ───
// Layout:  [Logo]  [spacer]  [stream stats]  [CONNECTED pill]  [Power button]
Rectangle {
    radius: height * 0.5
    clip: true
    color: Qt.rgba(0.06, 0.07, 0.11, 0.44)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.26)

    RowLayout {
        anchors { fill: parent; leftMargin: 18; rightMargin: 18 }
        spacing: 18

        // ── Brand ─────────────────────────────────────────────────────────
        Column {
            spacing: 2
            Layout.alignment: Qt.AlignVCenter

            Text {
                text: "OCCUSCOPE"
                font { pixelSize: 14; bold: true; letterSpacing: 1.2 }
                color: "#ffffff"
            }
            Text {
                text: "DIGITAL IMAGING SYSTEM"
                font { pixelSize: 8; letterSpacing: 0.9 }
                color: "#7888a0"
            }
        }

        Item { Layout.fillWidth: true }

        // ── Stream statistics ──────────────────────────────────────────────
        Text {
            text: bridge.statsText
            font { pixelSize: 12; weight: Font.Medium; letterSpacing: 0.3 }
            color: "#d8d8e6"
            Layout.alignment: Qt.AlignVCenter
        }

        // ── CONNECTED pill (ref: solid white + dark label when live) ────────
        Rectangle {
            height: 30
            width:  pillText.implicitWidth + 26
            radius: 15
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
                font { pixelSize: 10; bold: true; letterSpacing: 0.8 }
                color: bridge.connected ? "#1a1c22" : "#ff9090"
                Behavior on color { ColorAnimation { duration: 280 } }
            }
        }

        // ── Power button ───────────────────────────────────────────────────
        Rectangle {
            id: powerBtn
            width: 42; height: 42; radius: 21
            color: pwrMa.pressed       ? "#d0d0d8"
                 : pwrMa.containsMouse ? "#ffffff"
                 :                       Qt.rgba(1, 1, 1, 0.92)
            Layout.alignment: Qt.AlignVCenter
            Behavior on color { ColorAnimation { duration: 100 } }

            Image {
                anchors.centerIn: parent
                source:    Qt.resolvedUrl("icons/power.svg")
                sourceSize: Qt.size(20, 20)
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
