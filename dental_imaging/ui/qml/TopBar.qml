import QtQuick
import QtQuick.Layouts

// Top chrome strip: logo | stats | CONNECTED pill | power button
Rectangle {
    id: root
    color: Qt.rgba(0.08, 0.09, 0.11, 0.72)

    // Subtle bottom border
    Rectangle {
        anchors { left: parent.left; right: parent.right; bottom: parent.bottom }
        height: 1
        color:  Qt.rgba(1, 1, 1, 0.09)
    }

    RowLayout {
        id: barLayout
        anchors { fill: parent; leftMargin: 18; rightMargin: 18 }
        spacing: 20

        // App name / sub-name exposed as context properties from Python
        readonly property string _name:    (typeof appName    !== "undefined") ? appName    : "DENTAL IMAGING"
        readonly property string _subName: (typeof appSubName !== "undefined") ? appSubName : "SYSTEM"

        // ── Logo ──────────────────────────────────────────────────────────
        Column {
            spacing: 2
            Layout.alignment: Qt.AlignVCenter

            Text {
                text:               barLayout._name
                font.pixelSize:     14
                font.bold:          true
                font.letterSpacing: 0.8
                color:              "#ffffff"
            }
            Text {
                text:               barLayout._subName
                font.pixelSize:     9
                font.letterSpacing: 0.5
                color:              "#9090a0"
            }
        }

        Item { Layout.fillWidth: true }

        // ── Stream stats (plain text, no pill) ────────────────────────────
        Text {
            text:               bridge.statsText
            font.pixelSize:     13
            font.weight:        Font.Medium
            font.letterSpacing: 0.4
            color:              "#e4e4e4"
            Layout.alignment:   Qt.AlignVCenter
        }

        // ── CONNECTED pill ────────────────────────────────────────────────
        Rectangle {
            width:  connText.implicitWidth + 28
            height: 32
            radius: 16
            color:  bridge.connected ? Qt.rgba(1, 1, 1, 0.18) : Qt.rgba(1, 1, 1, 0.10)
            border.width: 1
            border.color: bridge.connected ? Qt.rgba(1, 1, 1, 0.55) : Qt.rgba(1, 1, 1, 0.25)
            Layout.alignment: Qt.AlignVCenter

            Behavior on color        { ColorAnimation { duration: 250 } }
            Behavior on border.color { ColorAnimation { duration: 250 } }

            Text {
                id:               connText
                anchors.centerIn: parent
                text:             bridge.connected ? "CONNECTED" : "DISCONNECTED"
                font.pixelSize:   11
                font.bold:        true
                font.letterSpacing: 0.6
                color:            bridge.connected ? "#ffffff" : "#c0c0c8"
                Behavior on color { ColorAnimation { duration: 250 } }
            }
        }

        // ── Power button (round white circle + dark icon) ─────────────────
        Rectangle {
            id:     powerCircle
            width:  44
            height: 44
            radius: 22
            color:  powerArea.pressed       ? "#d4d4dc"
                  : powerArea.containsMouse ? "#ffffff"
                  :                           Qt.rgba(1, 1, 1, 0.92)
            Layout.alignment: Qt.AlignVCenter

            Behavior on color { ColorAnimation { duration: 100 } }

            // Power SVG — Qt renders currentColor as black on a light background
            Image {
                anchors.centerIn: parent
                source:           Qt.resolvedUrl("icons/power.svg")
                sourceSize:       Qt.size(22, 22)
                fillMode:         Image.PreserveAspectFit
            }

            MouseArea {
                id:           powerArea
                anchors.fill: parent
                hoverEnabled: true
                cursorShape:  Qt.PointingHandCursor
                onClicked:    bridge.onPowerClicked()
            }

            scale: powerArea.pressed ? 0.90 : 1.0
            Behavior on scale { NumberAnimation { duration: 80 } }
        }
    }
}
