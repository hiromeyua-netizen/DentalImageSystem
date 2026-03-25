import QtQuick
import QtQuick.Layouts

// Label + pill toggle (off = white knob left on grey track).
RowLayout {
    id: root
    property string label: ""
    property bool   active: false
    signal toggled(bool v)

    Layout.fillWidth: true
    spacing: 12

    Text {
        text: root.label
        font.pixelSize: 13
        color: Qt.rgba(1, 1, 1, 0.92)
        Layout.fillWidth: true
        wrapMode: Text.WordWrap
    }

    Item {
        Layout.preferredWidth: 52
        Layout.preferredHeight: 30

        Rectangle {
            anchors.centerIn: parent
            width: 50
            height: 28
            radius: 14
            color: root.active ? Qt.rgba(0.52, 0.52, 0.58, 1) : Qt.rgba(0.38, 0.38, 0.44, 1)
            border.width: 1
            border.color: Qt.rgba(1, 1, 1, 0.12)

            Rectangle {
                width: 22
                height: 22
                radius: 11
                color: "#ffffff"
                x: root.active ? parent.width - width - 3 : 3
                anchors.verticalCenter: parent.verticalCenter
                Behavior on x { NumberAnimation { duration: 120; easing.type: Easing.OutCubic } }
            }
        }

        MouseArea {
            anchors.fill: parent
            cursorShape: Qt.PointingHandCursor
            onClicked: root.toggled(!root.active)
        }
    }
}
