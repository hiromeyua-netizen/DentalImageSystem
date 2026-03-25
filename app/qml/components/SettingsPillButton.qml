import QtQuick

// Single pill: outline when inactive, frosted fill when active.
Rectangle {
    id: pill
    property string text: ""
    property bool   active: false

    signal clicked()

    implicitWidth: Math.max(72, txt.implicitWidth + 28)
    implicitHeight: 40
    radius: height / 2
    // Frosted “selected” (ref image 2); outline only when off
    color: active ? Qt.rgba(1, 1, 1, 0.30) : "transparent"
    border.width: 1
    border.color: active ? Qt.rgba(1, 1, 1, 0.42) : Qt.rgba(1, 1, 1, 0.55)

    Text {
        id: txt
        anchors.centerIn: parent
        text: pill.text
        font.pixelSize: 12
        font.bold: true
        font.letterSpacing: 0.5
        color: "#ffffff"
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: pill.clicked()
    }
}
