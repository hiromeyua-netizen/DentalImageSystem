import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    // ── API ───────────────────────────────────────────────────────────────
    property color chromeBg
    property color chromeBorder
    property bool  captureEnabled:  false
    property bool  autoColorActive: false
    property bool  roiModeActive:   false

    // Readable state for main.qml
    property bool imageSettingsChecked: true
    property bool settingsChecked:      false

    signal flipH()
    signal flipV()
    signal rotateCW()
    signal rotateCCW()
    signal capture()
    signal recenterROI()
    signal imageSettingsToggled(bool open)
    signal settingsToggled(bool open)
    signal autoColorToggled(bool on)
    signal roiModeToggled(bool on)

    // ── Metrics ────────────────────────────────────────────────────────────
    readonly property int btnSz: Math.max(40, Math.round(width * 0.55))
    readonly property int iconPx: Math.max(16, Math.round(btnSz * 0.44))
    readonly property int pairBtnSz: Math.max(30, Math.round(btnSz * 0.68))
    readonly property int pairIconPx: Math.max(12, Math.round(pairBtnSz * 0.44))

    // ── Background ────────────────────────────────────────────────────────
    Rectangle {
        anchors.fill: parent
        color: root.chromeBg
        border.color: root.chromeBorder
        border.width: 1

        ColumnLayout {
            anchors { fill: parent; margins: Math.max(6, root.width * 0.08) }
            spacing: Math.max(6, root.height * 0.014)

            // ── Helper components ─────────────────────────────────────────

            // Single icon button
            component RailBtn: Rectangle {
                property string  glyph: ""
                property string  tip: ""
                property bool    checkable: false
                property bool    checked: false
                property bool    enabled: true
                property color   checkedColor: Qt.rgba(1,1,1,0.16)

                signal clicked()
                signal toggled(bool on)

                width:  root.btnSz;  height: root.btnSz
                radius: Math.max(6, width * 0.18)
                color:  checked ? checkedColor
                      : (btnMA.pressed ? Qt.rgba(1,1,1,0.20)
                      : (btnMA.containsMouse ? Qt.rgba(1,1,1,0.12)
                      : Qt.rgba(1,1,1,0.0)))
                border.color: checked ? Qt.rgba(1,1,1,0.30) : "transparent"
                border.width: 1
                opacity: enabled ? 1.0 : 0.38

                Behavior on color { ColorAnimation { duration: 110 } }

                Text {
                    anchors.centerIn: parent
                    text: parent.glyph
                    color: parent.checked ? "#ffffff" : Qt.rgba(1,1,1,0.78)
                    font.pixelSize: root.iconPx
                    font.family: "Segoe UI Symbol, Segoe UI, Arial"
                    horizontalAlignment: Text.AlignHCenter
                    verticalAlignment:   Text.AlignVCenter
                }
                MouseArea {
                    id: btnMA
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: parent.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
                    enabled: parent.enabled
                    onClicked: {
                        if (parent.checkable) {
                            parent.checked = !parent.checked
                            parent.toggled(parent.checked)
                        } else {
                            parent.clicked()
                        }
                    }
                }
                ToolTip.visible: btnMA.containsMouse && tip !== ""
                ToolTip.text: tip
                ToolTip.delay: 500
            }

            // Pair row (two smaller buttons side by side)
            component PairRow: Row {
                property string glyph1: ""; property string tip1: ""
                property string glyph2: ""; property string tip2: ""
                signal b1Clicked(); signal b2Clicked()

                spacing: Math.max(4, root.width * 0.05)
                Layout.alignment: Qt.AlignHCenter

                Rectangle {
                    property alias containsMouse: p1MA.containsMouse
                    width: root.pairBtnSz; height: root.pairBtnSz
                    radius: Math.max(5, width * 0.18)
                    color: p1MA.pressed ? Qt.rgba(1,1,1,0.20)
                         : (p1MA.containsMouse ? Qt.rgba(1,1,1,0.12) : Qt.rgba(1,1,1,0.0))
                    Behavior on color { ColorAnimation { duration: 110 } }
                    Text {
                        anchors.centerIn: parent
                        text: parent.parent.glyph1
                        color: Qt.rgba(1,1,1,0.78)
                        font.pixelSize: root.pairIconPx
                        font.family: "Segoe UI Symbol, Segoe UI, Arial"
                    }
                    MouseArea { id: p1MA; anchors.fill: parent; hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: parent.parent.b1Clicked() }
                    ToolTip.visible: p1MA.containsMouse
                    ToolTip.text: parent.tip1; ToolTip.delay: 500
                }

                Rectangle {
                    property alias containsMouse: p2MA.containsMouse
                    width: root.pairBtnSz; height: root.pairBtnSz
                    radius: Math.max(5, width * 0.18)
                    color: p2MA.pressed ? Qt.rgba(1,1,1,0.20)
                         : (p2MA.containsMouse ? Qt.rgba(1,1,1,0.12) : Qt.rgba(1,1,1,0.0))
                    Behavior on color { ColorAnimation { duration: 110 } }
                    Text {
                        anchors.centerIn: parent
                        text: parent.parent.glyph2
                        color: Qt.rgba(1,1,1,0.78)
                        font.pixelSize: root.pairIconPx
                        font.family: "Segoe UI Symbol, Segoe UI, Arial"
                    }
                    MouseArea { id: p2MA; anchors.fill: parent; hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: parent.parent.b2Clicked() }
                    ToolTip.visible: p2MA.containsMouse
                    ToolTip.text: parent.tip2; ToolTip.delay: 500
                }
            }

            // ── Actual buttons ────────────────────────────────────────────

            // Flip pair
            PairRow {
                Layout.alignment: Qt.AlignHCenter
                glyph1: "\u25BD\u25B2"; tip1: "Flip vertical"
                glyph2: "\u25B7\u25C1"; tip2: "Flip horizontal"
                onB1Clicked: root.flipV()
                onB2Clicked: root.flipH()
            }

            // Rotate pair
            PairRow {
                Layout.alignment: Qt.AlignHCenter
                glyph1: "\u25A1\u21BB"; tip1: "Rotate clockwise"
                glyph2: "\u25A1\u21BA"; tip2: "Rotate counter-clockwise"
                onB1Clicked: root.rotateCW()
                onB2Clicked: root.rotateCCW()
            }

            // Thin separator
            Rectangle { Layout.fillWidth: true; height: 1; color: Qt.rgba(1,1,1,0.08) }

            // Image settings toggle
            RailBtn {
                Layout.alignment: Qt.AlignHCenter
                glyph: "\uD83D\uDDBC"   // 🖼
                tip: "Image settings"
                checkable: true
                checked: root.imageSettingsChecked
                checkedColor: Qt.rgba(1,1,1,0.18)
                onToggled: function(on) {
                    root.imageSettingsChecked = on
                    root.imageSettingsToggled(on)
                }
            }

            // Settings toggle
            RailBtn {
                Layout.alignment: Qt.AlignHCenter
                glyph: "\u2699"   // ⚙
                tip: "Settings"
                checkable: true
                checked: root.settingsChecked
                checkedColor: Qt.rgba(1,1,1,0.18)
                onToggled: function(on) {
                    root.settingsChecked = on
                    root.settingsToggled(on)
                }
            }

            // Capture
            RailBtn {
                Layout.alignment: Qt.AlignHCenter
                glyph: "\uD83D\uDCF7"   // 📷
                tip: "Capture image"
                enabled: root.captureEnabled
                onClicked: root.capture()
            }

            // Auto colour
            RailBtn {
                Layout.alignment: Qt.AlignHCenter
                glyph: "\uD83C\uDF0D"   // 🌍
                tip: "Auto colour balance"
                checkable: true
                checked: root.autoColorActive
                checkedColor: Qt.rgba(0.35, 0.67, 0.43, 0.45)
                onToggled: function(on) {
                    root.autoColorActive = on
                    root.autoColorToggled(on)
                }
            }

            // Recenter ROI
            RailBtn {
                Layout.alignment: Qt.AlignHCenter
                glyph: "\u2295"   // ⊕
                tip: "Recenter ROI"
                onClicked: root.recenterROI()
            }

            // ROI mode
            RailBtn {
                Layout.alignment: Qt.AlignHCenter
                glyph: "\u229E"   // ⊞
                tip: "ROI mode"
                checkable: true
                checked: root.roiModeActive
                checkedColor: Qt.rgba(0.31, 0.55, 0.86, 0.42)
                onToggled: function(on) {
                    root.roiModeActive = on
                    root.roiModeToggled(on)
                }
            }

            Item { Layout.fillHeight: true }
        }
    }
}
