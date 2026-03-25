import QtQuick

// Horizontal slider with a white circular thumb that shows the value percentage.
// Signal userChanged(v) fires only on user drag — safe to bind to bridge slots.
Item {
    id: root

    property int value:   0
    property int minimum: 0
    property int maximum: 100

    signal userChanged(int v)

    // Slightly smaller thumb on compact layouts (BottomBar passes this).
    property real thumbRadius: 18

    implicitWidth:  200
    implicitHeight: _r * 2 + 8

    readonly property real _r: thumbRadius
    readonly property real _m: _r          // track left/right inset

    // Track
    Rectangle {
        anchors {
            left: parent.left; right: parent.right
            leftMargin: root._m; rightMargin: root._m
            verticalCenter: parent.verticalCenter
        }
        height: 4; radius: 2
        color: Qt.rgba(1, 1, 1, 0.15)

        // Filled portion
        Rectangle {
            width:  Math.max(0, thumb.x + root._r - root._m)
            height: parent.height; radius: 2
            color:  Qt.rgba(1, 1, 1, 0.50)
        }
    }

    // Thumb
    Rectangle {
        id: thumb
        width: root._r * 2; height: root._r * 2; radius: root._r
        color: "white"
        anchors.verticalCenter: parent.verticalCenter

        x: {
            var f = (root.value - root.minimum) / Math.max(1, root.maximum - root.minimum)
            return root._m + f * (root.width - 2 * root._m) - root._r
        }
        Behavior on x { NumberAnimation { duration: 55; easing.type: Easing.OutCubic } }

        Text {
            anchors.centerIn: parent
            text: root.value + "%"
            font.pixelSize: root._r < 17 ? 9 : 10
            font.bold: true
            color: "#16161e"
        }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape:  Qt.PointingHandCursor
        onPressed:         (e) => _update(e.x)
        onPositionChanged: (e) => { if (pressed) _update(e.x) }
    }

    function _update(mx) {
        var f = Math.max(0, Math.min(1, (mx - _m) / (width - 2 * _m)))
        var v = Math.round(minimum + f * (maximum - minimum))
        if (v !== value) { value = v; root.userChanged(v) }
    }
}
