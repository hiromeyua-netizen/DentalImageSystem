import QtQuick
import QtQuick.Layouts

// Image Settings row — root MUST be Item + anchored Column so width from ColumnLayout
// is non-zero (plain Column + Layout.fillWidth left track width 0 → no visible sliders).
Item {
    id: row
    Layout.fillWidth: true
    implicitHeight: inner.implicitHeight

    property string label: ""
    property int    value: 50
    signal moved(int v)

    Column {
        id: inner
        anchors { left: parent.left; right: parent.right; top: parent.top }
        spacing: 5

        Text {
            width: inner.width
            text: row.label
            font.pixelSize: 13
            font.weight: Font.Normal
            color: Qt.rgba(1, 1, 1, 0.95)
        }

        Item {
            id: track
            width: inner.width
            height: 36
            implicitHeight: 36

            readonly property real _r: 16
            readonly property real _m: _r + 2
            readonly property real _tw: Math.max(0, width - 2 * _m)
            readonly property real _cx: _m + (row.value / 100) * _tw

            Rectangle {
                x: track._m
                anchors.verticalCenter: parent.verticalCenter
                width: Math.max(0, track._cx - track._m)
                height: 3
                radius: 1.5
                color: Qt.rgba(0.50, 0.51, 0.56, 1)
            }
            Rectangle {
                x: track._cx
                anchors.verticalCenter: parent.verticalCenter
                width: Math.max(0, track._m + track._tw - track._cx)
                height: 3
                radius: 1.5
                color: Qt.rgba(1, 1, 1, 0.42)
            }

            Rectangle {
                id: thumb
                width: track._r * 2
                height: track._r * 2
                radius: track._r
                color: Qt.rgba(0.30, 0.31, 0.36, 1)
                border.width: 1
                border.color: Qt.rgba(1, 1, 1, 0.14)
                anchors.verticalCenter: parent.verticalCenter
                x: track._m + (row.value / 100) * track._tw - track._r
                Behavior on x { NumberAnimation { duration: 55; easing.type: Easing.OutCubic } }

                Text {
                    anchors.centerIn: parent
                    text: row.value + "%"
                    font.pixelSize: 9
                    font.bold: true
                    color: "#ffffff"
                }
            }

            // Arrow handlers do not see sibling `function _upd` — call `track._upd` explicitly.
            function _upd(mx) {
                var f = Math.max(0, Math.min(1, (mx - track._m) / Math.max(1, track._tw)))
                var v = Math.round(f * 100)
                if (v !== row.value)
                    row.moved(v)
            }

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onPressed: function (e) { track._upd(e.x) }
                onPositionChanged: function (e) {
                    if (pressed)
                        track._upd(e.x)
                }
            }
        }
    }
}
