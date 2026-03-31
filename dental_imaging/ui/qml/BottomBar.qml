import QtQuick
import QtQuick.Layouts
import "components"

// Bottom chrome bar: brightness slider | zoom slider | preset chips
Rectangle {
    id: root
    color: Qt.rgba(0.08, 0.09, 0.11, 0.72)

    // Top separator line
    Rectangle {
        anchors { left: parent.left; right: parent.right; top: parent.top }
        height: 1
        color:  Qt.rgba(1, 1, 1, 0.09)
    }

    RowLayout {
        anchors {
            fill:         parent
            leftMargin:   24
            rightMargin:  24
            topMargin:    8
            bottomMargin: 10
        }
        spacing: 32

        // ── Brightness section ────────────────────────────────────────────
        RowLayout {
            spacing: 10
            Layout.fillWidth: true

            Image {
                source:     Qt.resolvedUrl("icons/sun.svg")
                sourceSize: Qt.size(18, 18)
                fillMode:   Image.PreserveAspectFit
                opacity:    0.70
            }

            CircleSlider {
                Layout.fillWidth: true
                minimum:    0
                maximum:    100
                value:      bridge.brightness
                onUserChanged: (v) => bridge.onBrightnessChanged(v)
            }

            Image {
                source:     Qt.resolvedUrl("icons/sun.svg")
                sourceSize: Qt.size(24, 24)
                fillMode:   Image.PreserveAspectFit
                opacity:    0.90
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
                opacity:    0.78
            }

            CircleSlider {
                Layout.fillWidth: true
                minimum:    0
                maximum:    100
                value:      bridge.zoom
                onUserChanged: (v) => bridge.onZoomChanged(v)
            }

            Image {
                source:     Qt.resolvedUrl("icons/zoom_in.svg")
                sourceSize: Qt.size(20, 20)
                fillMode:   Image.PreserveAspectFit
                opacity:    0.78
            }
        }

        // ── Presets section ───────────────────────────────────────────────
        Column {
            spacing: 5
            Layout.alignment: Qt.AlignVCenter

            Text {
                text:               "Presets"
                font.pixelSize:     9
                font.letterSpacing: 0.4
                color:              "#9090a0"
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
