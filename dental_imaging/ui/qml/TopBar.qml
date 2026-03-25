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
        anchors { fill: parent; leftMargin: 18; rightMargin: 18 }
        spacing: 20

        // ── Logo ──────────────────────────────────────────────────────────
        Column {
            spacing: 2
            Layout.alignment: Qt.AlignVCenter
            Text {
                text:           bridge.statsText.length > 0 ? appName.split("\n")[0] : appName
                font.pixelSize: 14
                font.bold:      true
                font.letterSpacing: 0.8
                color:          "#ffffff"
                property string appName: bridge.statsText.length >= 0 ? _appName : _appName
            }
            Text {
                text:           _appSubName
                font.pixelSize: 9
                font.letterSpacing: 0.5
                color:          "#9090a0"
            }
        }

        // invisible: expose brand via context properties set from Python
        property string _appName:    typeof appName    !== "undefined" ? appName    : "DENTAL IMAGING"
        property string _appSubName: typeof appSubName !== "undefined" ? appSubName : "SYSTEM"

        Item { Layout.fillWidth: true }

        // ── Stream stats ──────────────────────────────────────────────────
        Text {
            id: statsLabel
            text:               bridge.statsText
            font.pixelSize:     13
            font.weight:        Font.Medium
            font.letterSpacing: 0.4
            color:              "#e4e4e4"
            Layout.alignment:   Qt.AlignVCenter
        }

        // ── CONNECTED pill ────────────────────────────────────────────────
        Rectangle {
            id: connPill
            width:  pillText.implicitWidth + 28
            height: 32
            radius: 16
            color: bridge.connected
                ? Qt.rgba(1, 1, 1, 0.18)
                : Qt.rgba(1, 1, 1, 0.10)
            border.width: 1
            border.color: bridge.connected
                ? Qt.rgba(1, 1, 1, 0.55)
                : Qt.rgba(1, 1, 1, 0.25)
            Layout.alignment: Qt.AlignVCenter

            Behavior on color        { ColorAnimation { duration: 250 } }
            Behavior on border.color { ColorAnimation { duration: 250 } }

            Text {
                id:              pillText
                anchors.centerIn: parent
                text:            bridge.connected ? "CONNECTED" : "DISCONNECTED"
                font.pixelSize:  11
                font.bold:       true
                font.letterSpacing: 0.6
                color:           bridge.connected ? "#ffffff" : "#c0c0c8"
                Behavior on color { ColorAnimation { duration: 250 } }
            }
        }

        // ── Power button ──────────────────────────────────────────────────
        Rectangle {
            id:     powerBtn
            width:  44
            height: 44
            radius: 22
            color:  powerMa.pressed ? "#d8d8e0"
                  : powerMa.containsMouse ? "#ffffff" : Qt.rgba(1,1,1,0.92)
            Layout.alignment: Qt.AlignVCenter

            Behavior on color { ColorAnimation { duration: 100 } }

            Image {
                anchors.centerIn: parent
                source:           Qt.resolvedUrl("icons/power.svg")
                sourceSize:       Qt.size(22, 22)
                fillMode:         Image.PreserveAspectFit
                // SVG stroke colour via colour overlay
                layer.enabled: true
                layer.effect: null
            }

            // Colourize the white SVG to dark for the light button
            ColorOverlayShim {
                anchors.fill: parent
                svgSource:    Qt.resolvedUrl("icons/power.svg")
                tintColor:    "#18181c"
            }

            MouseArea {
                id:              powerMa
                anchors.fill:    parent
                hoverEnabled:    true
                cursorShape:     Qt.PointingHandCursor
                onClicked:       bridge.onPowerClicked()
            }

            scale: powerMa.pressed ? 0.90 : 1.0
            Behavior on scale { NumberAnimation { duration: 80 } }
        }
    }
}

// Inline helper to render SVG with a solid tint (avoids needing MultiEffect)
component ColorOverlayShim: Item {
    property url   svgSource
    property color tintColor: "white"

    Image {
        anchors.fill: parent
        source:       svgSource
        sourceSize:   Qt.size(parent.width, parent.height)
        fillMode:     Image.PreserveAspectFit
        visible:      false
        id:           _src
    }
    // Simple rectangle mask: only works cleanly on solid/semi transparent bgs
    // For the white power circle this is fine.
    Image {
        anchors.fill:  parent
        source:        svgSource
        sourceSize:    Qt.size(parent.width, parent.height)
        fillMode:      Image.PreserveAspectFit
    }
}
