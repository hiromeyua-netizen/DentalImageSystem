import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    signal close()
    signal showGridChanged(bool v)
    signal showCrosshairChanged(bool v)
    signal autoScaleChanged(bool v)
    signal exportScopeChanged(string v)
    signal captureFormatChanged(string v)
    signal jpegQualityChanged(int v)
    signal captureModeChanged(string v)
    signal burstDelayChanged(int v)
    signal cameraSoundChanged(bool v)
    signal storageTargetChanged(string v)

    function syncValues(vals) {
        gridToggle.checked       = vals.showGrid       !== undefined ? vals.showGrid       : false
        crosshairToggle.checked  = vals.showCrosshair  !== undefined ? vals.showCrosshair  : false
        autoScaleToggle.checked  = vals.autoScale      !== undefined ? vals.autoScale      : true
        fullResToggle.checked    = vals.exportFullRes  !== undefined ? vals.exportFullRes  : true
        jpegQSlider.value        = vals.jpegQuality    !== undefined ? vals.jpegQuality    : 94
        soundToggle.checked      = vals.cameraSound    !== undefined ? vals.cameraSound    : true
        // Format
        var fmtIdx = ["jpeg","png"].indexOf(vals.captureFormat || "jpeg")
        formatCombo.currentIndex = fmtIdx >= 0 ? fmtIdx : 0
        // Capture mode
        var modeIdx = ["single","burst"].indexOf(vals.captureModeBurst ? "burst" : "single")
        modeCombo.currentIndex = vals.captureModeBurst ? 1 : 0
        burstDelaySpin.value = vals.burstDelaySec !== undefined ? vals.burstDelaySec : 10
    }

    opacity: visible ? 1.0 : 0.0
    Behavior on opacity { NumberAnimation { duration: 180; easing.type: Easing.OutQuad } }

    Rectangle {
        anchors.fill: parent
        anchors.topMargin: 12
        radius: 16
        color: Qt.rgba(0.12, 0.13, 0.16, 0.88)
        border.color: Qt.rgba(1,1,1,0.13)
        border.width: 1

        ColumnLayout {
            anchors { fill: parent; margins: 16 }
            spacing: 8

            // Header
            RowLayout {
                Layout.fillWidth: true
                Text { text: "Settings"; color: "#ffffff"; font.pixelSize: 15; font.weight: Font.DemiBold; font.family: "Segoe UI" }
                Item { Layout.fillWidth: true }
                Rectangle {
                    width: 26; height: 26; radius: 6
                    color: closeMA.pressed ? Qt.rgba(1,1,1,0.22) : (closeMA.containsMouse ? Qt.rgba(1,1,1,0.14) : Qt.rgba(1,1,1,0.08))
                    Behavior on color { ColorAnimation { duration: 100 } }
                    Text { anchors.centerIn: parent; text: "✕"; color: "#c8c8d8"; font.pixelSize: 12 }
                    MouseArea { id: closeMA; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.close() }
                }
            }
            Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(1,1,1,0.10) }

            // Fully custom toggle (no Switch control — avoids platform DLL dependency)
            component ToggleRow: RowLayout {
                id: trRoot
                property string label: ""
                property bool   checked: false
                signal toggled(bool v)
                Layout.fillWidth: true

                Text { text: trRoot.label; color: "#c0c0d0"; font.pixelSize: 12; font.family: "Segoe UI"; Layout.fillWidth: true }

                Rectangle {
                    id: track
                    width: 40; height: 22; radius: 11
                    color: trRoot.checked ? Qt.rgba(0.35,0.67,0.43,0.70) : Qt.rgba(1,1,1,0.18)
                    Behavior on color { ColorAnimation { duration: 150 } }

                    Rectangle {
                        id: thumb
                        x: trRoot.checked ? 20 : 2; y: 2; width: 18; height: 18; radius: 9
                        color: "#f0f0f8"
                        Behavior on x { NumberAnimation { duration: 150; easing.type: Easing.OutQuad } }
                    }

                    MouseArea {
                        anchors.fill: parent
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {
                            trRoot.checked = !trRoot.checked
                            trRoot.toggled(trRoot.checked)
                        }
                    }
                }
            }

            Flickable {
                Layout.fillWidth: true; Layout.fillHeight: true
                contentHeight: settingsCol.implicitHeight
                clip: true
                ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                ColumnLayout {
                    id: settingsCol; width: parent.width; spacing: 10

                    // Preview
                    Text { text: "Preview"; color: "#888898"; font.pixelSize: 10; font.family: "Segoe UI" }
                    ToggleRow { id: gridToggle;      label: "Show grid";       onToggled: root.showGridChanged(v) }
                    ToggleRow { id: crosshairToggle; label: "Show crosshair";  onToggled: root.showCrosshairChanged(v) }
                    ToggleRow { id: autoScaleToggle; label: "Auto-scale preview"; onToggled: root.autoScaleChanged(v) }

                    Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(1,1,1,0.08) }

                    // Capture
                    Text { text: "Capture"; color: "#888898"; font.pixelSize: 10; font.family: "Segoe UI" }
                    ToggleRow { id: fullResToggle; label: "Full resolution export";
                        onToggled: root.exportScopeChanged(v ? "full" : "preview") }

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Format"; color: "#c0c0d0"; font.pixelSize: 12; font.family: "Segoe UI"; Layout.fillWidth: true }
                        ComboBox {
                            id: formatCombo
                            model: ["JPEG", "PNG"]
                            font.pixelSize: 11
                            onCurrentIndexChanged: root.captureFormatChanged(currentIndex === 0 ? "jpeg" : "png")
                            background: Rectangle { radius: 6; color: Qt.rgba(1,1,1,0.12); border.color: Qt.rgba(1,1,1,0.20); border.width: 1 }
                            contentItem: Text { text: formatCombo.displayText; color: "#d8d8e8"; font: formatCombo.font; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                        }
                    }

                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "JPEG quality"; color: "#c0c0d0"; font.pixelSize: 12; font.family: "Segoe UI"; Layout.fillWidth: true }
                        Slider {
                            id: jpegQSlider; from: 50; to: 100; stepSize: 1; value: 94
                            implicitWidth: 120
                            onValueChanged: root.jpegQualityChanged(Math.round(value))
                            background: Rectangle {
                                x: jpegQSlider.leftPadding; y: jpegQSlider.topPadding + jpegQSlider.availableHeight/2 - height/2
                                width: jpegQSlider.availableWidth; height: 4; radius: 2; color: Qt.rgba(1,1,1,0.18)
                                Rectangle { width: jpegQSlider.visualPosition*parent.width; height: parent.height; radius: parent.radius; color: Qt.rgba(1,1,1,0.55) }
                            }
                            handle: Rectangle {
                                x: jpegQSlider.leftPadding + jpegQSlider.visualPosition*(jpegQSlider.availableWidth-width)
                                y: jpegQSlider.topPadding + jpegQSlider.availableHeight/2 - height/2
                                width: 18; height: 18; radius: 9; color: "#f0f0f8"
                            }
                        }
                        Text { text: Math.round(jpegQSlider.value)+"%" ; color: "#888898"; font.pixelSize: 11; Layout.minimumWidth: 32 }
                    }

                    Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(1,1,1,0.08) }

                    // Mode
                    Text { text: "Mode"; color: "#888898"; font.pixelSize: 10; font.family: "Segoe UI" }
                    RowLayout {
                        Layout.fillWidth: true
                        Text { text: "Capture mode"; color: "#c0c0d0"; font.pixelSize: 12; font.family: "Segoe UI"; Layout.fillWidth: true }
                        ComboBox {
                            id: modeCombo; model: ["Single", "Burst"]; font.pixelSize: 11
                            onCurrentIndexChanged: root.captureModeChanged(currentIndex === 0 ? "single" : "burst")
                            background: Rectangle { radius: 6; color: Qt.rgba(1,1,1,0.12); border.color: Qt.rgba(1,1,1,0.20); border.width: 1 }
                            contentItem: Text { text: modeCombo.displayText; color: "#d8d8e8"; font: modeCombo.font; leftPadding: 8; verticalAlignment: Text.AlignVCenter }
                        }
                    }

                    RowLayout {
                        visible: modeCombo.currentIndex === 1
                        Layout.fillWidth: true
                        Text { text: "Burst interval (s)"; color: "#c0c0d0"; font.pixelSize: 12; font.family: "Segoe UI"; Layout.fillWidth: true }
                        SpinBox {
                            id: burstDelaySpin; from: 1; to: 60; value: 10
                            onValueChanged: root.burstDelayChanged(value)
                            contentItem: Text { text: burstDelaySpin.textFromValue(burstDelaySpin.value); color: "#d8d8e8"; font.pixelSize: 12; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                            background: Rectangle { radius: 6; color: Qt.rgba(1,1,1,0.12); border.color: Qt.rgba(1,1,1,0.20); border.width: 1 }
                        }
                    }

                    ToggleRow { id: soundToggle; label: "Camera shutter sound"; onToggled: root.cameraSoundChanged(v) }
                }
            }
        }
    }
}
