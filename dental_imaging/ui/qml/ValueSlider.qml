import QtQuick
import QtQuick.Controls

// Custom horizontal slider: translucent groove + white circular thumb with % inside
Item {
    id: root
    height: thumbRadius * 2 + 8
    implicitHeight: height

    property int thumbRadius:  18
    property int grooveHeight: 5
    property int value:        0       // 0–100
    property int minimum:      0
    property int maximum:      100

    // Emitted only when the user drags (not on programmatic value updates)
    signal userMoved(int v)

    // ── Groove ────────────────────────────────────────────────────────────
    Rectangle {
        id: groove
        anchors.verticalCenter: parent.verticalCenter
        x:      root.thumbRadius + 2
        width:  Math.max(0, parent.width - 2 * (root.thumbRadius + 2))
        height: root.grooveHeight
        radius: root.grooveHeight / 2
        color:  Qt.rgba(1, 1, 1, 0.18)
    }

    // ── Thumb ─────────────────────────────────────────────────────────────
    Rectangle {
        id: thumb
        width:  root.thumbRadius * 2
        height: root.thumbRadius * 2
        radius: root.thumbRadius
        anchors.verticalCenter: parent.verticalCenter

        // Position = left edge of groove + fraction * (groove width - thumb width)
        x: {
            var frac = (root.value - root.minimum) / Math.max(1, root.maximum - root.minimum)
            var travelW = Math.max(0, groove.width - thumb.width)
            return groove.x + frac * travelW
        }

        color: Qt.rgba(1, 1, 1, 0.95)
        border.color: Qt.rgba(0.6, 0.6, 0.65, 0.4)
        border.width: 1

        layer.enabled: true
        layer.effect: null   // shadow via border only (no import needed)

        Text {
            anchors.centerIn: parent
            text: root.value + "%"
            color: "#202228"
            font.pixelSize: Math.max(8, root.thumbRadius - 4)
            font.bold: true
            font.family: "Segoe UI, Arial"
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment:   Text.AlignVCenter
        }
    }

    // ── Mouse interaction ─────────────────────────────────────────────────
    MouseArea {
        id: ma
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor

        function valueFromX(mx) {
            var clampedX = Math.max(groove.x, Math.min(groove.x + groove.width, mx))
            var frac = (clampedX - groove.x) / Math.max(1, groove.width)
            return Math.round(root.minimum + frac * (root.maximum - root.minimum))
        }

        onPressed:  function(mouse) { root.value = valueFromX(mouse.x); root.userMoved(root.value) }
        onPositionChanged: function(mouse) {
            if (pressed) { root.value = valueFromX(mouse.x); root.userMoved(root.value) }
        }
    }
}
