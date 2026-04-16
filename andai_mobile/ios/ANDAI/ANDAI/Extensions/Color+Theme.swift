import SwiftUI

extension Color {
    static let appPrimary = Color(hex: "dc2626")
    static let appPrimaryHover = Color(hex: "b91c1c")
    static let appPrimaryLight = Color(hex: "fef2f2")
    static let appAccent = Color(hex: "f97316")
    
    static let sidebarBg = Color(hex: "1a1a2e")
    static let sidebarHover = Color(hex: "16213e")
    static let deepBlue = Color(hex: "0f3460")
    
    static let bgMain = Color(hex: "f8fafc")
    static let bgCard = Color.white
    
    static let textPrimary = Color(hex: "1e293b")
    static let textSecondary = Color(hex: "64748b")
    
    static let border = Color(hex: "e2e8f0")
    
    static let slate50 = Color(hex: "f8fafc")
    static let slate100 = Color(hex: "f1f5f9")
    static let slate200 = Color(hex: "e2e8f0")
    static let slate300 = Color(hex: "cbd5e1")
    static let slate400 = Color(hex: "94a3b8")
    static let slate500 = Color(hex: "64748b")
    static let slate600 = Color(hex: "475569")
    static let slate700 = Color(hex: "334155")
    
    static let red50 = Color(hex: "fef2f2")
    static let red100 = Color(hex: "fee2e2")
    static let red200 = Color(hex: "fecaca")
    static let red400 = Color(hex: "f87171")
    static let red600 = Color(hex: "dc2626")
    static let red700 = Color(hex: "b91c1c")
    
    static let emerald50 = Color(hex: "ecfdf5")
    static let emerald200 = Color(hex: "a7f3d0")
    static let emerald600 = Color(hex: "059669")
    static let emerald700 = Color(hex: "047857")
    
    static let blue50 = Color(hex: "eff6ff")
    static let blue200 = Color(hex: "bfdbfe")
    static let blue600 = Color(hex: "2563eb")
    static let blue700 = Color(hex: "1d4ed8")
    
    static let amber50 = Color(hex: "fffbeb")
    static let amber200 = Color(hex: "fde68a")
    static let amber600 = Color(hex: "d97706")
    static let amber700 = Color(hex: "b45309")
    
    static let purple50 = Color(hex: "faf5ff")
    static let purple300 = Color(hex: "d8b4fe")
    static let purple700 = Color(hex: "7c3aed")
    
    static let violet50 = Color(hex: "f5f3ff")
    static let violet600 = Color(hex: "7c3aed")
    
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(.sRGB, red: Double(r) / 255, green: Double(g) / 255, blue: Double(b) / 255, opacity: Double(a) / 255)
    }
}
