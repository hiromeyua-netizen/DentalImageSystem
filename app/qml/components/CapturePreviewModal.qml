import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape

    width: Math.max(760, Math.round((Window.window ? Window.window.width : 1280) * 0.90))
    height: Math.max(420, Math.round((Window.window ? Window.window.height : 720) * 0.72))
    x: Math.round(((Window.window ? Window.window.width : 1280) - width) / 2)
    y: Math.round(((Window.window ? Window.window.height : 720) - height) / 2)

    function selectedItem() {
        const i = bridge.capturePreviewIndex
        const arr = bridge.captureItems
        if (!arr || i < 0 || i >= arr.length)
            return null
        return arr[i]
    }

    background: Rectangle {
        radius: 20
        color: Qt.rgba(0.06, 0.06, 0.08, 0.42)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.28)
    }

    contentItem: Item {
        anchors.fill: parent
        anchors.margins: 18

        RowLayout {
            anchors.fill: parent
            spacing: 16

            // Left preview
            ColumnLayout {
                Layout.preferredWidth: Math.round(parent.width * 0.36)
                Layout.fillHeight: true
                spacing: 10

                Text {
                    text: "Capture Preview"
                    font.pixelSize: 22
                    font.bold: true
                    color: "#ffffff"
                    Layout.bottomMargin: 6
                }

                Rectangle {
                    Layout.fillWidth: true
                    height: 1
                    color: Qt.rgba(1, 1, 1, 0.16)
                    Layout.bottomMargin: 6
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 14
                    color: Qt.rgba(0, 0, 0, 0.18)
                    border.width: 1
                    border.color: Qt.rgba(1, 1, 1, 0.28)
                    clip: true

                    Image {
                        anchors.fill: parent
                        anchors.margins: 8
                        fillMode: Image.PreserveAspectFit
                        source: {
                            const it = root.selectedItem()
                            return it ? String(it.url || "") : ""
                        }
                        smooth: true
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: {
                        const it = root.selectedItem()
                        return it ? String(it.name || "") : "No image selected"
                    }
                    font.pixelSize: 18
                    font.bold: true
                    color: "#ffffff"
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    text: {
                        const it = root.selectedItem()
                        return it ? String(it.datetime || "") : ""
                    }
                    font.pixelSize: 13
                    color: Qt.rgba(1, 1, 1, 0.75)
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Button {
                        text: "Previous"
                        enabled: bridge.capturePreviewIndex > 0
                        onClicked: bridge.onCapturePreviewPrevious()
                        background: Rectangle {
                            radius: 14
                            color: parent.enabled ? Qt.rgba(1, 1, 1, 0.10) : Qt.rgba(1, 1, 1, 0.04)
                            border.width: 1
                            border.color: Qt.rgba(1, 1, 1, 0.30)
                        }
                        contentItem: Text {
                            text: parent.text
                            color: parent.enabled ? "#ffffff" : Qt.rgba(1, 1, 1, 0.45)
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.pixelSize: 13
                            font.weight: Font.Medium
                        }
                    }
                    Button {
                        text: "Next"
                        enabled: bridge.capturePreviewIndex >= 0
                                 && bridge.capturePreviewIndex < bridge.captureItems.length - 1
                        onClicked: bridge.onCapturePreviewNext()
                        background: Rectangle {
                            radius: 14
                            color: parent.enabled ? Qt.rgba(1, 1, 1, 0.10) : Qt.rgba(1, 1, 1, 0.04)
                            border.width: 1
                            border.color: Qt.rgba(1, 1, 1, 0.30)
                        }
                        contentItem: Text {
                            text: parent.text
                            color: parent.enabled ? "#ffffff" : Qt.rgba(1, 1, 1, 0.45)
                            horizontalAlignment: Text.AlignHCenter
                            verticalAlignment: Text.AlignVCenter
                            font.pixelSize: 13
                            font.weight: Font.Medium
                        }
                    }
                }
            }

            // Right thumbnails grid
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 14
                color: Qt.rgba(0, 0, 0, 0.16)
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.24)
                clip: true

                GridView {
                    id: gallery
                    anchors.fill: parent
                    anchors.margins: 10
                    model: bridge.captureItems
                    cellWidth: Math.floor((width - 3 * 10) / 4)
                    cellHeight: Math.round(cellWidth * 0.86)
                    clip: true
                    interactive: true
                    boundsBehavior: Flickable.StopAtBounds

                    delegate: Item {
                        required property int index
                        required property var modelData
                        readonly property var item: modelData

                        width: gallery.cellWidth
                        height: gallery.cellHeight

                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.top: parent.top
                            height: Math.round(parent.height * 0.78)
                            radius: 8
                            color: Qt.rgba(1, 1, 1, 0.08)
                            border.width: bridge.capturePreviewIndex === index ? 2 : 1
                            border.color: bridge.capturePreviewIndex === index
                                ? Qt.rgba(1, 1, 1, 0.95)
                                : Qt.rgba(1, 1, 1, 0.26)

                            Image {
                                anchors.fill: parent
                                anchors.margins: 4
                                fillMode: Image.PreserveAspectCrop
                                source: String(item.url || "")
                                smooth: true
                            }
                        }

                        Text {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            text: String(item.name || "")
                            color: Qt.rgba(1, 1, 1, 0.78)
                            font.pixelSize: 11
                            horizontalAlignment: Text.AlignHCenter
                            elide: Text.ElideRight
                        }

                        MouseArea {
                            anchors.fill: parent
                            cursorShape: Qt.PointingHandCursor
                            onClicked: bridge.onCapturePreviewSelect(index)
                        }
                    }
                }

                Text {
                    anchors.centerIn: parent
                    visible: bridge.captureItems.length === 0
                    text: "No captured images"
                    color: Qt.rgba(1, 1, 1, 0.75)
                    font.pixelSize: 14
                }
            }
        }

        ToolButton {
            anchors.right: parent.right
            anchors.top: parent.top
            text: "✕"
            font.pixelSize: 18
            background: Rectangle {
                radius: 12
                color: parent.hovered ? Qt.rgba(1, 1, 1, 0.10) : "transparent"
                border.width: parent.hovered ? 1 : 0
                border.color: Qt.rgba(1, 1, 1, 0.24)
            }
            contentItem: Text {
                text: parent.text
                color: Qt.rgba(1, 1, 1, 0.86)
                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
                font.pixelSize: 18
                font.bold: true
            }
            onClicked: bridge.onCapturePreviewClose()
        }
    }

    onOpened: bridge.onCapturePreviewRefresh()
}

