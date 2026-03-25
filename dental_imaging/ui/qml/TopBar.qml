import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    // ── API ───────────────────────────────────────────────────────────────
    property color  chromeBg
    property color  chromeBorder
    property string brandTitle: "DENTAL IMAGING"
    property string statsText:  "— X —     — fps     — MB/s"
    property bool   connected:  false

    signal powerClicked()

    // ── Background ────────────────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        color: root.chromeBg
        border.color: root.chromeBorder
        border.width: 1

        RowLayout {
            anchors { fill: parent; leftMargin: 20; rightMargin: 16; topMargin: 0; bottomMargin: 0 }
            spacing: 16

            // ── Brand ─────────────────────────────────────────────────────
            Column {
                spacing: 1
                Layout.alignment: Qt.AlignVCenter

                Text {
                    text: {
                        var parts = root.brandTitle.split(" — ")
                        return parts[0].toUpperCase()
                    }
                    color: "#ffffff"
                    font.pixelSize: Math.max(13, root.height * 0.28)
                    font.weight: Font.Bold
                    font.letterSpacing: 0.8
                    font.family: "Segoe UI, Arial"
                }
                Text {
                    visible: root.brandTitle.indexOf(" — ") !== -1
                    text: {
                        var parts = root.brandTitle.split(" — ")
                        return parts.length > 1 ? parts[1].toUpperCase() : ""
                    }
                    color: "#888898"
                    font.pixelSize: Math.max(8, root.height * 0.14)
                    font.letterSpacing: 0.4
                    font.family: "Segoe UI, Arial"
                }
            }

            // ── Stretch ───────────────────────────────────────────────────
            Item { Layout.fillWidth: true }

            // ── Stream stats ──────────────────────────────────────────────
            Text {
                text: root.statsText
                color: "#dddde8"
                font.pixelSize: Math.max(11, root.height * 0.22)
                font.family: "Consolas, Segoe UI, monospace"
                font.letterSpacing: 0.3
                Layout.alignment: Qt.AlignVCenter
            }

            // ── CONNECTED pill ────────────────────────────────────────────
            Rectangle {
                id: connPill
                width:  connText.implicitWidth + 32
                height: Math.max(28, root.height * 0.50)
                radius: height / 2
                color:  root.connected ? Qt.rgba(1,1,1,0.17) : Qt.rgba(1,1,1,0.08)
                border.color: root.connected ? Qt.rgba(1,1,1,0.55) : Qt.rgba(1,1,1,0.25)
                border.width: 1
                Layout.alignment: Qt.AlignVCenter

                Behavior on color        { ColorAnimation { duration: 250 } }
                Behavior on border.color { ColorAnimation { duration: 250 } }

                Text {
                    id: connText
                    anchors.centerIn: parent
                    text: root.connected ? "CONNECTED" : "DISCONNECTED"
                    color: root.connected ? "#ffffff" : "#b0b0be"
                    font.pixelSize: Math.max(10, root.height * 0.19)
                    font.weight: Font.Bold
                    font.letterSpacing: 0.6
                    font.family: "Segoe UI, Arial"

                    Behavior on color { ColorAnimation { duration: 250 } }
                }
            }

            // ── Power button (white circle) ────────────────────────────────
            Rectangle {
                id: powerBtn
                width:  Math.max(38, root.height * 0.70)
                height: width
                radius: width / 2
                color:  powerMa.pressed ? "#d4d4dc" : (powerMa.containsMouse ? "#ffffff" : "#eeeeF2")
                Layout.alignment: Qt.AlignVCenter

                Behavior on color { ColorAnimation { duration: 120 } }

                Text {
                    anchors.centerIn: parent
                    text: "\u23FB"   // ⏻
                    color: "#1a1a22"
                    font.pixelSize: Math.max(16, parent.height * 0.48)
                    font.weight: Font.Bold
                    font.family: "Segoe UI Symbol, Segoe UI"
                }

                MouseArea {
                    id: powerMa
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: root.powerClicked()
                }

                ToolTip.visible: powerMa.containsMouse
                ToolTip.text: root.connected ? "Disconnect camera" : "Connect camera"
                ToolTip.delay: 600
            }
        }
    }
}
