import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root

    // Data in
    property string capturePath: ""
    property int captureW: 0
    property int captureH: 0

    // Behavior
    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    // Layout
    width: Math.min(520, Math.max(320, (Window.window ? Window.window.width : 1280) * 0.44))
    x: Math.round(((Window.window ? Window.window.width : 1280) - width) / 2)
    y: Math.round(((Window.window ? Window.window.height : 720) - height) / 2)

    readonly property string _normPath: (capturePath || "").replace(/\\/g, "/")
    readonly property string _fileName: {
        var p = _normPath
        var idx = p.lastIndexOf("/")
        return (idx >= 0) ? p.substring(idx + 1) : p
    }
    readonly property string _dirPath: {
        var p = _normPath
        var idx = p.lastIndexOf("/")
        return (idx >= 0) ? p.substring(0, idx) : p
    }

    function openFolder() {
        if (!_dirPath)
            return
        Qt.openUrlExternally("file:///" + _dirPath)
    }

    function openFile() {
        if (!_normPath)
            return
        Qt.openUrlExternally("file:///" + _normPath)
    }

    background: Rectangle {
        radius: 16
        color: Qt.rgba(0.10, 0.10, 0.12, 0.94)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.18)
    }

    contentItem: ColumnLayout {
        spacing: 12
        anchors.fill: parent
        anchors.margins: 16

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Rectangle {
                width: 34
                height: 34
                radius: 10
                color: Qt.rgba(0.35, 0.75, 0.45, 0.18)
                border.width: 1
                border.color: Qt.rgba(0.35, 0.75, 0.45, 0.25)

                Text {
                    anchors.centerIn: parent
                    text: "✓"
                    font.pixelSize: 18
                    font.bold: true
                    color: Qt.rgba(0.70, 1.0, 0.78, 0.95)
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2

                Text {
                    text: "Capture saved"
                    font.pixelSize: 16
                    font.bold: true
                    color: "#ffffff"
                    Layout.fillWidth: true
                    wrapMode: Text.Wrap
                }

                Text {
                    text: (captureW > 0 && captureH > 0) ? (captureW + " × " + captureH) : ""
                    font.pixelSize: 12
                    color: Qt.rgba(1, 1, 1, 0.72)
                    Layout.fillWidth: true
                    visible: text.length > 0
                }
            }

            ToolButton {
                text: "✕"
                onClicked: root.close()
                font.pixelSize: 14
                Layout.alignment: Qt.AlignTop
            }
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Qt.rgba(1, 1, 1, 0.10)
        }

        ColumnLayout {
            Layout.fillWidth: true
            spacing: 6

            Text {
                text: _fileName
                font.pixelSize: 13
                font.bold: true
                color: Qt.rgba(1, 1, 1, 0.92)
                Layout.fillWidth: true
                elide: Text.ElideRight
            }

            Text {
                text: _normPath
                font.pixelSize: 12
                color: Qt.rgba(1, 1, 1, 0.70)
                Layout.fillWidth: true
                elide: Text.ElideMiddle
            }
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Button {
                text: "Open File"
                enabled: _normPath.length > 0
                onClicked: root.openFile()
            }

            Button {
                text: "Open Folder"
                enabled: _dirPath.length > 0
                onClicked: root.openFolder()
            }

            Item { Layout.fillWidth: true }

            Button {
                text: "OK"
                onClicked: root.close()
                highlighted: true
            }
        }
    }
}

