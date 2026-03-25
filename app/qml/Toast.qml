import QtQuick

// Brief fade-in / fade-out notification.  Call show("message") to display.
Rectangle {
    id: root
    visible:      false
    opacity:      0
    height:       40
    width:        label.implicitWidth + 36
    radius:       10
    color:        Qt.rgba(0.09, 0.10, 0.14, 0.96)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.14)

    Text {
        id: label
        anchors.centerIn: parent
        font.pixelSize:   13
        color:            "#eeeef4"
    }

    SequentialAnimation {
        id: anim
        NumberAnimation { target: root; property: "opacity"; to: 1.0; duration: 190 }
        PauseAnimation  { duration: 2300 }
        NumberAnimation { target: root; property: "opacity"; to: 0.0; duration: 280 }
        ScriptAction    { script: root.visible = false }
    }

    function show(text) {
        label.text = text
        visible    = true
        anim.restart()
    }
}
