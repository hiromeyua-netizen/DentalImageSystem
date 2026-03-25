import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    // ── API ───────────────────────────────────────────────────────────────
    property color chromeBg
    property color chromeBorder
    property int   brightness:   50
    property int   zoom:         0
    property int   activePreset: -1    // -1 = none

    // "Edited" = user moved the slider; "Changed" suffix is reserved for property notifications
    signal brightnessEdited(int v)
    signal zoomEdited(int v)
    signal presetClicked(int n)
    signal presetSaveReq(int n)

    // Sync slider when Python pushes new values (e.g. preset applied)
    onBrightnessChanged: { if (brSlider.value !== brightness) brSlider.value = brightness }
    onZoomChanged:       { if (zmSlider.value !== zoom)       zmSlider.value = zoom }

    // ── Metrics ────────────────────────────────────────────────────────────
    readonly property int thumbR:   Math.max(16, Math.round(height * 0.22))
    readonly property int grooveH:  Math.max(4,  Math.round(height * 0.055))
    readonly property int chipSz:   Math.max(42, Math.round(height * 0.54))
    readonly property int glyphPx:  Math.max(14, Math.round(height * 0.20))
    readonly property int glyphLgPx:Math.max(18, Math.round(height * 0.26))

    // ── Background ────────────────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        color:        root.chromeBg
        border.color: root.chromeBorder
        border.width: 1

        RowLayout {
            anchors { fill: parent; leftMargin: 20; rightMargin: 20; topMargin: 8; bottomMargin: 10 }
            spacing: 28

            // ── Brightness section ─────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                // Small sun
                Text {
                    text: "\u2600"
                    color: Qt.rgba(1,1,1,0.72)
                    font.pixelSize: root.glyphPx
                    font.family: "Segoe UI Symbol, Segoe UI"
                    Layout.alignment: Qt.AlignVCenter
                }

                // Custom slider
                ValueSlider {
                    id: brSlider
                    Layout.fillWidth: true
                    thumbRadius: root.thumbR
                    grooveHeight: root.grooveH
                    value: root.brightness
                    onUserMoved: root.brightnessEdited(v)
                }

                // Large sun
                Text {
                    text: "\u2600"
                    color: Qt.rgba(1,1,1,0.90)
                    font.pixelSize: root.glyphLgPx
                    font.family: "Segoe UI Symbol, Segoe UI"
                    Layout.alignment: Qt.AlignVCenter
                }
            }

            // ── Zoom section ───────────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                // Zoom out
                Text {
                    text: "\u2296"  // ⊖
                    color: Qt.rgba(1,1,1,0.78)
                    font.pixelSize: root.glyphPx
                    font.family: "Segoe UI Symbol, Segoe UI"
                    Layout.alignment: Qt.AlignVCenter
                }

                ValueSlider {
                    id: zmSlider
                    Layout.fillWidth: true
                    thumbRadius: root.thumbR
                    grooveHeight: root.grooveH
                    value: root.zoom
                    onUserMoved: root.zoomEdited(v)
                }

                // Zoom in
                Text {
                    text: "\u2295"  // ⊕
                    color: Qt.rgba(1,1,1,0.90)
                    font.pixelSize: root.glyphLgPx
                    font.family: "Segoe UI Symbol, Segoe UI"
                    Layout.alignment: Qt.AlignVCenter
                }
            }

            // ── Presets section ────────────────────────────────────────────
            ColumnLayout {
                spacing: 4
                Layout.alignment: Qt.AlignVCenter

                Text {
                    text: "Presets"
                    color: "#808090"
                    font.pixelSize: Math.max(9, root.height * 0.10)
                    font.family: "Segoe UI, Arial"
                    Layout.alignment: Qt.AlignHCenter
                }

                RowLayout {
                    spacing: 8

                    Repeater {
                        model: 3

                        Rectangle {
                            id: chip
                            property int idx: index
                            property bool isActive: root.activePreset === index

                            width: root.chipSz; height: root.chipSz
                            radius: width / 2
                            color: isActive ? Qt.rgba(1,1,1,0.22)
                                 : (chipMA.containsMouse ? Qt.rgba(1,1,1,0.12)
                                 : Qt.rgba(1,1,1,0.0))
                            border.color: isActive ? Qt.rgba(1,1,1,0.75) : Qt.rgba(1,1,1,0.45)
                            border.width: isActive ? 2 : 1.5

                            Behavior on color        { ColorAnimation { duration: 150 } }
                            Behavior on border.color { ColorAnimation { duration: 150 } }

                            Text {
                                anchors.centerIn: parent
                                // ① ② ③
                                text: ["\u2460","\u2461","\u2462"][index]
                                color: chip.isActive ? "#ffffff" : Qt.rgba(1,1,1,0.72)
                                font.pixelSize: Math.max(15, root.chipSz * 0.48)
                                font.family: "Segoe UI Symbol, Segoe UI"

                                Behavior on color { ColorAnimation { duration: 150 } }
                            }

                            // Long-press timer
                            property var pressTimer: Timer {
                                interval: 700; repeat: false
                                onTriggered: { chip.longPressActive = true; root.presetSaveReq(chip.idx) }
                            }
                            property bool longPressActive: false

                            MouseArea {
                                id: chipMA
                                anchors.fill: parent
                                hoverEnabled: true
                                cursorShape: Qt.PointingHandCursor
                                onPressed: {
                                    chip.longPressActive = false
                                    chip.pressTimer.start()
                                }
                                onReleased: {
                                    chip.pressTimer.stop()
                                    if (!chip.longPressActive) root.presetClicked(chip.idx)
                                }
                                onCanceled: chip.pressTimer.stop()
                            }

                            ToolTip.visible: chipMA.containsMouse
                            ToolTip.text: "Tap: apply  •  Hold: save"
                            ToolTip.delay: 600
                        }
                    }
                }
            }
        }
    }
}
