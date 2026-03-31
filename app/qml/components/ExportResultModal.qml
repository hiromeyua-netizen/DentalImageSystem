import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Popup {
    id: root
    property string folderPath: ""
    property int exportedCount: 0
    property int renamedCount: 0
    property int failedCount: 0

    modal: true
    focus: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    width: Math.min(560, Math.max(340, (Window.window ? Window.window.width : 1280) * 0.46))
    x: Math.round(((Window.window ? Window.window.width : 1280) - width) / 2)
    y: Math.round(((Window.window ? Window.window.height : 720) - height) / 2)

    readonly property string _normFolder: (folderPath || "").replace(/\\/g, "/")

    function openFolder() {
        if (!_normFolder)
            return
        Qt.openUrlExternally("file:///" + _normFolder)
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

        Text {
            text: "Export completed"
            font.pixelSize: 17
            font.bold: true
            color: "#ffffff"
        }

        Rectangle {
            Layout.fillWidth: true
            height: 1
            color: Qt.rgba(1, 1, 1, 0.10)
        }

        Text {
            Layout.fillWidth: true
            text: "Exported: " + exportedCount + "    Renamed: " + renamedCount + "    Failed: " + failedCount
            font.pixelSize: 13
            color: Qt.rgba(1, 1, 1, 0.86)
            wrapMode: Text.WordWrap
        }

        Text {
            Layout.fillWidth: true
            text: _normFolder
            font.pixelSize: 12
            color: Qt.rgba(1, 1, 1, 0.68)
            elide: Text.ElideMiddle
        }

        Item { Layout.fillHeight: true }

        RowLayout {
            Layout.fillWidth: true
            spacing: 10

            Button {
                text: "Open Folder"
                enabled: _normFolder.length > 0
                onClicked: root.openFolder()
            }
            Item { Layout.fillWidth: true }
            Button {
                text: "OK"
                highlighted: true
                onClicked: root.close()
            }
        }
    }
}
