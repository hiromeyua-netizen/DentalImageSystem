import QtQuick
import QtQuick.Layouts
import QtQuick.Window
import "components"

// ── Bottom control bar — floating horizontal capsule (Occuscope ref) ──────────
Rectangle {
    id: bottomRoot
    radius: height * 0.5
    clip: true
    color: Qt.rgba(0.06, 0.07, 0.11, 0.44)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.26)

    readonly property var win: Window.window
    readonly property real _aw: win ? win.width : 1280
    readonly property bool _compact: _aw < 1100
    readonly property bool _narrow: _aw < 820

    readonly property real _lm: _narrow ? 12 : (_compact ? 16 : 22)
    readonly property real _sp: _narrow ? 10 : (_compact ? 14 : 20)
    readonly property real _ico: _narrow ? 14 : (_compact ? 15 : 16)
    readonly property real _thumbR: _narrow ? 14 : (_compact ? 15 : 18)

    RowLayout {
        anchors {
            fill: parent
            leftMargin: bottomRoot._lm
            rightMargin: bottomRoot._lm
            topMargin: bottomRoot._compact ? 8 : 10
            bottomMargin: bottomRoot._compact ? 8 : 10
        }
        spacing: bottomRoot._sp

        RowLayout {
            Layout.fillWidth: true
            spacing: bottomRoot._narrow ? 6 : 10

            Image {
                source: Qt.resolvedUrl("icons/sun.svg")
                sourceSize: Qt.size(bottomRoot._ico, bottomRoot._ico)
                fillMode: Image.PreserveAspectFit
                opacity: 0.60
            }
            ValueSlider {
                Layout.fillWidth: true
                thumbRadius: bottomRoot._thumbR
                value: bridge.brightness
                onUserChanged: (v) => bridge.onBrightnessChanged(v)
            }
            Image {
                source: Qt.resolvedUrl("icons/sun.svg")
                sourceSize: Qt.size(bottomRoot._ico + 4, bottomRoot._ico + 4)
                fillMode: Image.PreserveAspectFit
                opacity: 0.90
            }
        }

        RowLayout {
            Layout.fillWidth: true
            spacing: bottomRoot._narrow ? 6 : 10

            Image {
                source: Qt.resolvedUrl("icons/zoom_out.svg")
                sourceSize: Qt.size(bottomRoot._ico + 2, bottomRoot._ico + 2)
                fillMode: Image.PreserveAspectFit
                opacity: 0.72
            }
            ValueSlider {
                Layout.fillWidth: true
                thumbRadius: bottomRoot._thumbR
                value: bridge.zoom
                onUserChanged: (v) => bridge.onZoomChanged(v)
            }
            Image {
                source: Qt.resolvedUrl("icons/zoom_in.svg")
                sourceSize: Qt.size(bottomRoot._ico + 2, bottomRoot._ico + 2)
                fillMode: Image.PreserveAspectFit
                opacity: 0.72
            }
        }

        Item {
            Layout.preferredWidth: presetRow.width * presetRow.scale
            Layout.preferredHeight: presetRow.height * presetRow.scale
            Layout.alignment: Qt.AlignVCenter

            Row {
                id: presetRow
                anchors.centerIn: parent
                spacing: bottomRoot._narrow ? 6 : 8
                scale: bottomRoot._narrow ? 0.82 : (bottomRoot._compact ? 0.9 : 1.0)
                transformOrigin: Item.Center

                Repeater {
                    model: 3
                    delegate: PresetChip {
                        chipIndex: index
                        isActive: bridge.activePreset === index
                        onTapped: (i) => bridge.onPresetClicked(i)
                        onLongPress: (i) => bridge.onPresetSave(i)
                    }
                }
            }
        }
    }
}
