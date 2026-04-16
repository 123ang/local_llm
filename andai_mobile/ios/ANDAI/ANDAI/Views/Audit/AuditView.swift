import SwiftUI

struct AuditView: View {
    @EnvironmentObject var auth: AuthService
    @State private var logs: [AuditLog] = []
    @State private var isLoading = true
    
    var body: some View {
        VStack(spacing: 0) {
            VStack(alignment: .leading) {
                Text("Audit Logs").font(.system(size: 20, weight: .bold)).foregroundColor(.textPrimary)
                Text("Activity history").font(.system(size: 13)).foregroundColor(.textSecondary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
            .background(Color.bgCard)
            .overlay(Rectangle().fill(Color.border).frame(height: 1), alignment: .bottom)
            
            if isLoading {
                Spacer(); ProgressView().tint(.appPrimary); Spacer()
            } else if logs.isEmpty {
                Spacer()
                Image(systemName: "doc.plaintext").font(.system(size: 42)).foregroundColor(.slate300)
                Text("No audit logs").font(.system(size: 15, weight: .medium)).foregroundColor(.slate400).padding(.top, 8)
                Spacer()
            } else {
                List(logs) { log in
                    HStack(alignment: .top, spacing: 12) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 8).fill(actionBg(log.action)).frame(width: 34, height: 34)
                            Image(systemName: actionIcon(log.action)).font(.system(size: 14)).foregroundColor(actionColor(log.action))
                        }
                        
                        VStack(alignment: .leading, spacing: 2) {
                            Text(log.action)
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.textPrimary)
                            if let rt = log.resourceType {
                                Text("\(rt)\(log.resourceId != nil ? " #\(log.resourceId!)" : "")")
                                    .font(.system(size: 12))
                                    .foregroundColor(.textSecondary)
                            }
                            HStack(spacing: 6) {
                                if let email = log.userEmail {
                                    Text(email).font(.system(size: 11)).foregroundColor(.slate500).lineLimit(1)
                                }
                                Spacer()
                                if let date = log.createdAt {
                                    Text(formatDate(date)).font(.system(size: 11)).foregroundColor(.slate400)
                                }
                            }
                        }
                    }
                    .padding(.vertical, 4)
                }
                .listStyle(.plain)
                .refreshable { await loadLogs() }
            }
        }
        .background(Color.bgMain)
        .navigationBarHidden(true)
        .task { await loadLogs() }
    }
    
    private func actionIcon(_ action: String) -> String {
        let a = action.lowercased()
        if a.contains("create") { return "plus.circle" }
        if a.contains("update") { return "pencil" }
        if a.contains("delete") { return "trash" }
        if a.contains("login") { return "arrow.right.to.line" }
        if a.contains("upload") { return "icloud.and.arrow.up" }
        return "circle"
    }
    
    private func actionColor(_ action: String) -> Color {
        let a = action.lowercased()
        if a.contains("create") { return .emerald600 }
        if a.contains("update") { return .blue600 }
        if a.contains("delete") { return .red600 }
        if a.contains("login") { return .purple700 }
        if a.contains("upload") { return .amber600 }
        return .slate500
    }
    
    private func actionBg(_ action: String) -> Color {
        let a = action.lowercased()
        if a.contains("create") { return .emerald50 }
        if a.contains("update") { return .blue50 }
        if a.contains("delete") { return .red50 }
        if a.contains("login") { return .purple50 }
        if a.contains("upload") { return .amber50 }
        return .slate100
    }
    
    private func formatDate(_ dateStr: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        guard let date = formatter.date(from: dateStr) ?? ISO8601DateFormatter().date(from: dateStr) else { return dateStr }
        let display = DateFormatter()
        display.dateFormat = "MMM d, HH:mm"
        return display.string(from: date)
    }
    
    private func loadLogs() async {
        logs = (try? await APIService.shared.getAuditLogs(companyId: auth.companyId)) ?? []
        isLoading = false
    }
}
