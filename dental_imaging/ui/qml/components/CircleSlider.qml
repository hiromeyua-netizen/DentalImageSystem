import QtQuick
import QtQuick.Controls

// Horizontal slider with a white circular thumb that shows the value % inside.
// Signals: valueChanged(int)
Item {
    id: root

    property int  value:   0
    property int  minimum: 0
    property int  maximum: 100

    // userChanged carries the new value explicitly — avoids clash with the
    // auto-generated "valueChanged()" signal that Qt creates for every property.
    signal userChanged(int v)

    implicitHeight: thumbR * 2 + 8
    implicitWidth:  200

    readonly property real thumbR:  18
    readonly property real grooveH: 5
    readonly property real margin:  thumbR + 4

    // Track
    Rectangle {
        id: groove
        anchors.left:           parent.left
        anchors.right:          parent.right
        anchors.leftMargin:     root.margin
        anchors.rightMargin:    root.margin
        anchors.verticalCenter: parent.verticalCenter
        height: root.grooveH
        radius: root.grooveH / 2
        color:  Qt.rgba(1, 1, 1, 0.18)
    }

    // Thumb
    Rectangle {
        id: thumb
        width:  root.thumbR * 2
        height: root.thumbR * 2
        radius: root.thumbR
        color:  "white"
        anchors.verticalCenter: parent.verticalCenter

        property real frac: (root.value - root.minimum) / Math.max(1, root.maximum - root.minimum)

        x: root.margin + frac * (root.width - 2 * root.margin) - root.thumbR

        // Clamp
        onXChanged: {
            if (x < root.margin - root.thumbR)
                x = root.margin - root.thumbR
        }

        Behavior on x { NumberAnimation { duration: 60; easing.type: Easing.OutCubic } }

        // Value text inside thumb
        Text {
            anchors.centerIn: parent
            text:             root.value + "%"
            font.pixelSize:   11
            font.bold:        true
            color:            "#1e1e24"
        }

        // Subtle shadow ring
        layer.enabled:    true
        layer.effect: null  // keep simple — no heavy effects
    }

    // Mouse / touch interaction
    MouseArea {
        anchors.fill: parent
        onPressed:    (mouse) => _updateFromX(mouse.x)
        onPositionChanged: (mouse) => { if (pressed) _updateFromX(mouse.x) }
        cursorShape:  Qt.PointingHandCursor
    }

    function _updateFromX(mx) {
        var trackW = width - 2 * margin
        var frac   = Math.min(1, Math.max(0, (mx - margin) / trackW))
        var v = Math.round(minimum + frac * (maximum - minimum))
        if (v !== value) {
            value = v
            root.userChanged(v)
        }
    }
}
