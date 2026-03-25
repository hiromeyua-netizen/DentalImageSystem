import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Effects

Item {
    id: root

    // ── API ───────────────────────────────────────────────────────────────
    signal close()
    signal resetClicked()
    signal exposureChanged(int v)
    signal gainChanged(int v)
    signal whiteBalanceChanged(int v)
    signal contrastChanged(int v)
    signal saturationChanged(int v)
    signal warmthChanged(int v)
    signal tintChanged(int v)

    // Called by main.qml when Python pushes new values
    function syncValues(vals) {
        exposureSlider.value     = vals.exposure     !== undefined ? vals.exposure     : 50
        gainSlider.value         = vals.gain         !== undefined ? vals.gain         : 50
        wbSlider.value           = vals.whiteBalance !== undefined ? vals.whiteBalance : 50
        contrastSlider.value     = vals.contrast     !== undefined ? vals.contrast     : 50
        saturationSlider.value   = vals.saturation   !== undefined ? vals.saturation   : 50
        warmthSlider.value       = vals.warmth       !== undefined ? vals.warmth       : 50
        tintSlider.value         = vals.tint         !== undefined ? vals.tint         : 50
    }

    // ── Metrics ───────────────────────────────────────────────────────────
    readonly property int rowH:    36
    readonly property int sliderH: 28
    readonly property real cornerR: 16

    // ── Entrance animation ─────────────────────────────────────────────────
    opacity: visible ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

    // ── Panel background (frosted glass style) ─────────────────────────────
    Rectangle {
        id: panelBg
        anchors.fill: parent
        anchors.topMargin: 12
        radius: root.cornerR
        color:  Qt.rgba(0.12, 0.13, 0.16, 0.88)
        border.color: Qt.rgba(1, 1, 1, 0.13)
        border.width: 1

        layer.enabled: true

        // Inner content
        ColumnLayout {
            anchors { fill: parent; margins: 16 }
            spacing: 8

            // ── Header ────────────────────────────────────────────────────
            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Text {
                    text: "Image Settings"
                    color: "#ffffff"
                    font.pixelSize: 15
                    font.weight: Font.DemiBold
                    font.family: "Segoe UI, Arial"
                }
                Item { Layout.fillWidth: true }

                // Reset button
                Rectangle {
                    width: resetText.implicitWidth + 20
                    height: 26
                    radius: 6
                    color: resetMA.pressed ? Qt.rgba(1,1,1,0.22)
                         : (resetMA.containsMouse ? Qt.rgba(1,1,1,0.14) : Qt.rgba(1,1,1,0.08))
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text {
                        id: resetText
                        anchors.centerIn: parent
                        text: "Reset"
                        color: "#c8c8d8"
                        font.pixelSize: 12
                        font.family: "Segoe UI, Arial"
                    }
                    MouseArea {
                        id: resetMA; anchors.fill: parent; hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: root.resetClicked()
                    }
                }

                // Close button
                Rectangle {
                    width: 26; height: 26; radius: 6
                    color: closeMA.pressed ? Qt.rgba(1,1,1,0.22)
                         : (closeMA.containsMouse ? Qt.rgba(1,1,1,0.14) : Qt.rgba(1,1,1,0.08))
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text { anchors.centerIn: parent; text: "✕"; color: "#c8c8d8"; font.pixelSize: 12 }
                    MouseArea { id: closeMA; anchors.fill: parent; hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor; onClicked: root.close() }
                }
            }

            // Separator
            Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(1,1,1,0.10) }

            // ── Sliders ───────────────────────────────────────────────────
            Flickable {
                Layout.fillWidth: true
                Layout.fillHeight: true
                contentHeight: sliderColumn.implicitHeight
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                ColumnLayout {
                    id: sliderColumn
                    width: parent.width
                    spacing: 6

                    component SliderRow: ColumnLayout {
                        property string label: ""
                        property alias  value: sl.value
                        signal sliderMoved(int v)
                        Layout.fillWidth: true
                        spacing: 3

                        RowLayout {
                            Layout.fillWidth: true
                            Text {
                                text: parent.parent.label
                                color: "#c0c0d0"
                                font.pixelSize: 11
                                font.family: "Segoe UI, Arial"
                                Layout.fillWidth: true
                            }
                            Text {
                                text: sl.value + "%"
                                color: "#888898"
                                font.pixelSize: 10
                                font.family: "Segoe UI, Arial"
                                horizontalAlignment: Text.AlignRight
                                Layout.minimumWidth: 32
                            }
                        }

                        // Native QML Slider styled to match reference
                        Slider {
                            id: sl
                            Layout.fillWidth: true
                            from: 0; to: 100
                            stepSize: 1
                            onMoved: parent.sliderMoved(Math.round(value))

                            background: Rectangle {
                                x: sl.leftPadding; y: sl.topPadding + sl.availableHeight / 2 - height / 2
                                width: sl.availableWidth; height: 5; radius: 2.5
                                color: Qt.rgba(1,1,1,0.18)
                                Rectangle {
                                    width: sl.visualPosition * parent.width
                                    height: parent.height; radius: parent.radius
                                    color: Qt.rgba(1,1,1,0.55)
                                }
                            }

                            handle: Rectangle {
                                x: sl.leftPadding + sl.visualPosition * (sl.availableWidth - width)
                                y: sl.topPadding + sl.availableHeight / 2 - height / 2
                                width: 22; height: 22; radius: 11
                                color: "#f0f0f8"
                                border.color: Qt.rgba(0.6,0.6,0.65,0.5)
                                border.width: 1
                            }
                        }
                    }

                    SliderRow { id: exposureSlider;   label: "Exposure";      onSliderMoved: function(v){ root.exposureChanged(v) } }
                    SliderRow { id: gainSlider;        label: "Gain";          onSliderMoved: function(v){ root.gainChanged(v) } }
                    SliderRow { id: wbSlider;          label: "White Balance"; onSliderMoved: function(v){ root.whiteBalanceChanged(v) } }
                    SliderRow { id: contrastSlider;    label: "Contrast";      onSliderMoved: function(v){ root.contrastChanged(v) } }
                    SliderRow { id: saturationSlider;  label: "Saturation";    onSliderMoved: function(v){ root.saturationChanged(v) } }
                    SliderRow { id: warmthSlider;      label: "Warmth";        onSliderMoved: function(v){ root.warmthChanged(v) } }
                    SliderRow { id: tintSlider;        label: "Tint";          onSliderMoved: function(v){ root.tintChanged(v) } }
                }
            }
        }
    }
}
