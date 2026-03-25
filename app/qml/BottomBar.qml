import QtQuick
import QtQuick.Layouts
import "components"

// ── Bottom control bar — floating horizontal capsule (Occuscope ref) ──────────
// Layout:  [small-sun | brightness-slider | big-sun]  [zoom-out | zoom-slider | zoom-in]  [Presets]
Rectangle {
    radius: height * 0.5
    clip: true
    color: Qt.rgba(0.06, 0.07, 0.11, 0.44)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.26)

    RowLayout {
        anchors { fill: parent; leftMargin: 22; rightMargin: 22; topMargin: 10; bottomMargin: 10 }
        spacing: 20

        // ── Brightness ────────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true; spacing: 10

            Image {
                source: Qt.resolvedUrl("icons/sun.svg"); sourceSize: Qt.size(16, 16)
                fillMode: Image.PreserveAspectFit; opacity: 0.60
            }
            ValueSlider {
                Layout.fillWidth: true
                value:   bridge.brightness
                onUserChanged: (v) => bridge.onBrightnessChanged(v)
            }
            Image {
                source: Qt.resolvedUrl("icons/sun.svg"); sourceSize: Qt.size(22, 22)
                fillMode: Image.PreserveAspectFit; opacity: 0.90
            }
        }

        // ── Zoom ──────────────────────────────────────────────────────────
        RowLayout {
            Layout.fillWidth: true; spacing: 10

            Image {
                source: Qt.resolvedUrl("icons/zoom_out.svg"); sourceSize: Qt.size(19, 19)
                fillMode: Image.PreserveAspectFit; opacity: 0.72
            }
            ValueSlider {
                Layout.fillWidth: true
                value:   bridge.zoom
                onUserChanged: (v) => bridge.onZoomChanged(v)
            }
            Image {
                source: Qt.resolvedUrl("icons/zoom_in.svg"); sourceSize: Qt.size(19, 19)
                fillMode: Image.PreserveAspectFit; opacity: 0.72
            }
        }

        // ── Presets ───────────────────────────────────────────────────────
        RowLayout {
            spacing: 8; Layout.alignment: Qt.AlignVCenter
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
