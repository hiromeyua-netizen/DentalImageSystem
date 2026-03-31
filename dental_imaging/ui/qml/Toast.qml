import QtQuick

// Animated toast notification that auto-hides after 2.5 s.
Rectangle {
    id: root
    visible:  false
    opacity:  0
    radius:   10
    color:    Qt.rgba(0.10, 0.11, 0.14, 0.94)
    border.width: 1
    border.color: Qt.rgba(1, 1, 1, 0.18)
    height:   42
    width:    msg.implicitWidth + 40

    Text {
        id:              msg
        anchors.centerIn: parent
        font.pixelSize:  13
        color:           "#f0f0f4"
    }

    // Appear animation
    SequentialAnimation {
        id: showAnim
        NumberAnimation { target: root; property: "opacity"; to: 1.0; duration: 200 }
        PauseAnimation  { duration: 2200 }
        NumberAnimation { target: root; property: "opacity"; to: 0.0; duration: 300 }
        ScriptAction    { script: root.visible = false }
    }

    function show(text) {
        msg.text = text
        visible  = true
        showAnim.restart()
    }
}
