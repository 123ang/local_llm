import SwiftUI

struct SettingsView: View {
    @EnvironmentObject var auth: AuthService
    @State private var companies: [Company] = []
    @State private var showCompanyPicker = false
    @State private var serverStatus: [String: Any]?
    @State private var loadingStatus = false
    @State private var showLogoutAlert = false
    
    var body: some View {
        ScrollView {
            VStack(spacing: 20) {
                // Profile
                VStack(spacing: 12) {
                    ZStack {
                        Circle().fill(Color.appPrimary).frame(width: 64, height: 64)
                        Text(String(auth.currentUser?.fullName.prefix(1) ?? "?").uppercased())
                            .font(.system(size: 26, weight: .bold))
                            .foregroundColor(.white)
                    }
                    Text(auth.currentUser?.fullName ?? "")
                        .font(.system(size: 18, weight: .bold))
                        .foregroundColor(.white)
                    Text(auth.currentUser?.email ?? "")
                        .font(.system(size: 13))
                        .foregroundColor(.slate400)
                    Text(auth.currentUser?.role.replacingOccurrences(of: "_", with: " ").uppercased() ?? "")
                        .font(.system(size: 11, weight: .bold))
                        .foregroundColor(.red400)
                        .padding(.horizontal, 10)
                        .padding(.vertical, 4)
                        .background(Color.red600.opacity(0.2))
                        .cornerRadius(20)
                }
                .frame(maxWidth: .infinity)
                .padding(24)
                .background(Color.sidebarBg)
                .cornerRadius(16)
                
                // Company switcher
                if auth.isSuperAdmin && !companies.isEmpty {
                    VStack(alignment: .leading, spacing: 8) {
                        sectionHeader("Active Company")
                        Button { showCompanyPicker = true } label: {
                            HStack {
                                Image(systemName: "building.2")
                                    .foregroundColor(.appPrimary)
                                Text(companies.first { $0.id == auth.companyId }?.name ?? "Select Company")
                                    .font(.system(size: 14, weight: .medium))
                                    .foregroundColor(.textPrimary)
                                Spacer()
                                Image(systemName: "chevron.down")
                                    .font(.system(size: 12))
                                    .foregroundColor(.slate400)
                            }
                            .padding(16)
                            .background(Color.bgCard)
                            .cornerRadius(16)
                            .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.border, lineWidth: 1))
                        }
                    }
                }
                
                // Server
                VStack(alignment: .leading, spacing: 8) {
                    sectionHeader("Server")
                    Button { checkStatus() } label: {
                        HStack {
                            Image(systemName: "waveform.path.ecg")
                                .foregroundColor(.emerald600)
                            Text("Check Server Status")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.textPrimary)
                            Spacer()
                            if loadingStatus { ProgressView().scaleEffect(0.8) }
                        }
                        .padding(16)
                        .background(Color.bgCard)
                        .cornerRadius(16)
                        .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.border, lineWidth: 1))
                    }
                    
                    if let status = serverStatus {
                        VStack(spacing: 8) {
                            if let ollama = status["ollama"] as? [String: Any] {
                                statusRow("Ollama", value: ollama["status"] as? String ?? "unknown")
                                if let models = ollama["models"] as? [[String: Any]] {
                                    statusRow("Models", value: models.compactMap { $0["name"] as? String }.joined(separator: ", "))
                                }
                            }
                            if let db = status["database"] as? [String: Any] {
                                statusRow("Database", value: db["status"] as? String ?? "unknown")
                            }
                        }
                        .padding(16)
                        .background(Color.bgCard)
                        .cornerRadius(12)
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.border, lineWidth: 1))
                    }
                }
                
                // About
                VStack(alignment: .leading, spacing: 8) {
                    sectionHeader("About")
                    aboutRow("App", value: "ANDAI Mobile v1.0.0")
                    aboutRow("Platform", value: "Adaptive Neural Decision AI")
                }
                
                // Logout
                Button { showLogoutAlert = true } label: {
                    HStack {
                        Image(systemName: "rectangle.portrait.and.arrow.right")
                        Text("Sign Out")
                    }
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.red600)
                    .frame(maxWidth: .infinity)
                    .padding(16)
                    .background(Color.bgCard)
                    .cornerRadius(16)
                    .overlay(RoundedRectangle(cornerRadius: 16).stroke(Color.red200, lineWidth: 1))
                }
            }
            .padding(16)
        }
        .background(Color.bgMain)
        .navigationTitle("Settings")
        .task {
            if auth.isSuperAdmin {
                companies = (try? await APIService.shared.getCompanies()) ?? []
            }
        }
        .alert("Sign Out", isPresented: $showLogoutAlert) {
            Button("Cancel", role: .cancel) {}
            Button("Sign Out", role: .destructive) { auth.logout() }
        } message: {
            Text("Are you sure you want to sign out?")
        }
        .confirmationDialog("Select Company", isPresented: $showCompanyPicker) {
            ForEach(companies) { c in
                Button(c.name) { auth.setCompanyId(c.id) }
            }
        }
    }
    
    private func sectionHeader(_ text: String) -> some View {
        Text(text)
            .font(.system(size: 11, weight: .semibold))
            .foregroundColor(.textSecondary)
            .textCase(.uppercase)
            .tracking(1)
            .padding(.horizontal, 4)
    }
    
    private func statusRow(_ label: String, value: String) -> some View {
        HStack {
            Text(label).font(.system(size: 13)).foregroundColor(.textSecondary)
            Spacer()
            Text(value)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(value == "connected" ? .emerald600 : .textPrimary)
                .lineLimit(2)
                .multilineTextAlignment(.trailing)
        }
    }
    
    private func aboutRow(_ label: String, value: String) -> some View {
        HStack {
            Text(label).font(.system(size: 13)).foregroundColor(.textSecondary)
            Spacer()
            Text(value).font(.system(size: 13, weight: .medium)).foregroundColor(.textPrimary)
        }
        .padding(16)
        .background(Color.bgCard)
        .cornerRadius(12)
        .overlay(RoundedRectangle(cornerRadius: 12).stroke(Color.border, lineWidth: 1))
    }
    
    private func checkStatus() {
        loadingStatus = true
        Task {
            serverStatus = try? await APIService.shared.getStatus()
            await MainActor.run { loadingStatus = false }
        }
    }
}
