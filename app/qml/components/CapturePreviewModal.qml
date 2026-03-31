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

    readonly property var items: bridge.captureItems
    readonly property int sel: bridge.capturePreviewIndex
    readonly property var selectedItem: (sel >= 0 && sel < items.length) ? items[sel] : null

    background: Rectangle {
        radius: 16
        color: Qt.rgba(0.86, 0.67, 0.68, 0.78)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.35)
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
                    font.pixelSize: 28
                    font.bold: true
                    color: "#ffffff"
                    Layout.bottomMargin: 8
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    radius: 14
                    color: Qt.rgba(0, 0, 0, 0.18)
                    border.width: 1
                    border.color: Qt.rgba(1, 1, 1, 0.22)
                    clip: true

                    Image {
                        anchors.fill: parent
                        anchors.margins: 8
                        fillMode: Image.PreserveAspectFit
                        source: root.selectedItem ? root.selectedItem.url : ""
                        smooth: true
                    }
                }

                Text {
                    Layout.fillWidth: true
                    text: root.selectedItem ? root.selectedItem.name : "No image selected"
                    font.pixelSize: 20
                    font.bold: true
                    color: "#ffffff"
                    elide: Text.ElideRight
                }
                Text {
                    Layout.fillWidth: true
                    text: root.selectedItem ? root.selectedItem.datetime : ""
                    font.pixelSize: 16
                    color: Qt.rgba(1, 1, 1, 0.88)
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 10
                    Button {
                        text: "Previous"
                        enabled: bridge.capturePreviewIndex > 0
                        onClicked: bridge.onCapturePreviewPrevious()
                    }
                    Button {
                        text: "Next"
                        enabled: bridge.capturePreviewIndex >= 0
                                 && bridge.capturePreviewIndex < bridge.captureItems.length - 1
                        onClicked: bridge.onCapturePreviewNext()
                    }
                }
            }

            // Right thumbnails grid
            Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                radius: 14
                color: Qt.rgba(0, 0, 0, 0.10)
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.16)
                clip: true

                Flickable {
                    id: flick
                    anchors.fill: parent
                    anchors.margins: 10
                    contentWidth: grid.width
                    contentHeight: grid.height
                    clip: true

                    Grid {
                        id: grid
                        columns: 4
                        spacing: 10
                        width: flick.width

                        Repeater {
                            model: bridge.captureItems.length
                            delegate: Rectangle {
                                required property int index
                                readonly property var item: bridge.captureItems[index]
                                width: Math.floor((grid.width - grid.spacing * (grid.columns - 1)) / grid.columns)
                                height: Math.round(width * 0.72)
                                radius: 8
                                color: Qt.rgba(1, 1, 1, 0.10)
                                border.width: bridge.capturePreviewIndex === index ? 2 : 1
                                border.color: bridge.capturePreviewIndex === index
                                    ? Qt.rgba(1, 1, 1, 0.95)
                                    : Qt.rgba(1, 1, 1, 0.22)

                                Image {
                                    anchors.fill: parent
                                    anchors.margins: 4
                                    fillMode: Image.PreserveAspectCrop
                                    source: item.url
                                    smooth: true
                                }

                                MouseArea {
                                    anchors.fill: parent
                                    cursorShape: Qt.PointingHandCursor
                                    onClicked: bridge.onCapturePreviewSelect(index)
                                }
                            }
                        }
                    }
                }
            }
        }

        ToolButton {
            anchors.right: parent.right
            anchors.top: parent.top
            text: "✕"
            font.pixelSize: 20
            onClicked: bridge.onCapturePreviewClose()
        }
    }
}

