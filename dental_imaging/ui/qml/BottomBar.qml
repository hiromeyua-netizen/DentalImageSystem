import QtQuick
import QtQuick.Layouts
import "components"

// Bottom chrome bar: brightness slider | zoom slider | preset chips
Rectangle {
    id: root
    color: Qt.rgba(0.08, 0.09, 0.11, 0.72)

    Rectangle {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 1
        color:  Qt.rgba(1, 1, 1, 0.09)
    }

    RowLayout {
        anchors { fill: parent; leftMargin: 24; rightMargin: 24; topMargin: 8; bottomMargin: 10 }
        spacing: 32

        // ── Brightness section ────────────────────────────────────────────
        RowLayout {
            spacing: 10
            Layout.fillWidth: true

            Image {
                source:     Qt.resolvedUrl("icons/sun.svg")
                sourceSize: Qt.size(18, 18)
                fillMode:   Image.PreserveAspectFit
                opacity:    0.72
            }

            CircleSlider {
                id:          brightnessSlider
                Layout.fillWidth: true
                minimum:    0
                maximum:    100
                value:      bridge.brightness
                onValueChanged: (v) => bridge.onBrightnessChanged(v)
            }

            Image {
                source:     Qt.resolvedUrl("icons/sun.svg")
                sourceSize: Qt.size(24, 24)
                fillMode:   Image.PreserveAspectFit
                opacity:    0.92
            }
        }

        // ── Zoom section ──────────────────────────────────────────────────
        RowLayout {
            spacing: 10
            Layout.fillWidth: true

            Image {
                source:     Qt.resolvedUrl("icons/zoom_out.svg")
                sourceSize: Qt.size(20, 20)
                fillMode:   Image.PreserveAspectFit
                opacity:    0.80
            }

            CircleSlider {
                id:          zoomSlider
                Layout.fillWidth: true
                minimum:    0
                maximum:    100
                value:      bridge.zoom
                onValueChanged: (v) => bridge.onZoomChanged(v)
            }

            Image {
                source:     Qt.resolvedUrl("icons/zoom_in.svg")
                sourceSize: Qt.size(20, 20)
                fillMode:   Image.PreserveAspectFit
                opacity:    0.80
            }
        }

        // ── Presets section ───────────────────────────────────────────────
        Column {
            spacing: 4
            Layout.alignment: Qt.AlignVCenter

            Text {
                text:           "Presets"
                font.pixelSize: 9
                font.letterSpacing: 0.4
                color:          "#9090a0"
                anchors.horizontalCenter: parent.horizontalCenter
            }

            RowLayout {
                spacing: 8

                Repeater {
                    model: 3

                    delegate: PresetChip {
                        chipIndex:   index
                        isActive:    bridge.activePreset === index
                        onTapped:    (i) => bridge.onPresetClicked(i)
                        onLongPress: (i) => bridge.onPresetSave(i)
                    }
                }
            }
        }
    }
}

// Inline preset chip component
component PresetChip: Rectangle {
    property int  chipIndex
    property bool isActive: false
    signal tapped(int i)
    signal longPress(int i)

    width:  50; height: 50
    radius: 25
    color:  isActive ? Qt.rgba(1,1,1,0.22) : "transparent"
    border.width: 2
    border.color: isActive ? Qt.rgba(1,1,1,0.80) : Qt.rgba(1,1,1,0.45)

    Behavior on color        { ColorAnimation { duration: 180 } }
    Behavior on border.color { ColorAnimation { duration: 180 } }

    Text {
        anchors.centerIn: parent
        text:             chipIndex + 1
        font.pixelSize:   18
        font.weight:      Font.Medium
        color:            isActive ? "#ffffff" : Qt.rgba(1,1,1,0.72)
    }

    scale: ma.pressed ? 0.88 : 1.0
    Behavior on scale { NumberAnimation { duration: 90; easing.type: Easing.OutBack } }

    property var _lpTimer: Timer {
        interval: 700
        repeat:   false
        onTriggered: {
            _fired = true
            longPress(chipIndex)
        }
    }
    property bool _fired: false

    MouseArea {
        id: ma
        anchors.fill: parent
        cursorShape:  Qt.PointingHandCursor
        onPressed:    { parent._fired = false; parent._lpTimer.start() }
        onReleased:   {
            parent._lpTimer.stop()
            if (!parent._fired) parent.tapped(chipIndex)
        }
        onCanceled:   parent._lpTimer.stop()
    }
}
