import QtQuick

// Floating toast notification that fades in/out
Rectangle {
    id: root
    width: toastText.implicitWidth + 40
    height: toastText.implicitHeight + 20
    radius: height / 2
    color: Qt.rgba(0.08, 0.09, 0.11, 0.88)
    border.color: Qt.rgba(1, 1, 1, 0.22)
    border.width: 1
    opacity: 0
    visible: opacity > 0

    Text {
        id: toastText
        anchors.centerIn: parent
        text: ""
        color: "#f0f0f8"
        font.pixelSize: 14
        font.family: "Segoe UI, Arial"
    }

    // Fade in then out
    SequentialAnimation {
        id: seq
        NumberAnimation { target: root; property: "opacity"; to: 1.0; duration: 180; easing.type: Easing.OutQuad }
        PauseAnimation  { id: holdPause; duration: 2400 }
        NumberAnimation { target: root; property: "opacity"; to: 0.0; duration: 350; easing.type: Easing.InQuad }
    }

    function show(message, durationMs) {
        seq.stop()
        toastText.text = message
        holdPause.duration = Math.max(800, (durationMs || 2800) - 530)
        seq.start()
    }
}
