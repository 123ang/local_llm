import SwiftUI

struct UsersView: View {
    @EnvironmentObject var auth: AuthService
    @State private var users: [UserItem] = []
    @State private var isLoading = true
    @State private var showForm = false
    @State private var editingUser: UserItem?
    
    var body: some View {
        VStack(spacing: 0) {
            HStack {
                VStack(alignment: .leading) {
                    Text("Users").font(.system(size: 20, weight: .bold)).foregroundColor(.textPrimary)
                    Text("Manage user accounts").font(.system(size: 13)).foregroundColor(.textSecondary)
                }
                Spacer()
                Button {
                    editingUser = nil
                    showForm = true
                } label: {
                    HStack(spacing: 4) {
                        Image(systemName: "person.badge.plus")
                        Text("Add")
                    }
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(.white)
                    .padding(.horizontal, 14).padding(.vertical, 8)
                    .background(Color.appPrimary).cornerRadius(10)
                }
            }
            .padding(16)
            .background(Color.bgCard)
            .overlay(Rectangle().fill(Color.border).frame(height: 1), alignment: .bottom)
            
            if isLoading {
                Spacer(); ProgressView().tint(.appPrimary); Spacer()
            } else {
                List(users) { u in
                    HStack(spacing: 12) {
                        ZStack {
                            Circle().fill(Color.sidebarBg).frame(width: 44, height: 44)
                            Text(String(u.fullName.prefix(1)).uppercased())
                                .font(.system(size: 18, weight: .bold))
                                .foregroundColor(.white)
                        }
                        VStack(alignment: .leading, spacing: 2) {
                            Text(u.fullName).font(.system(size: 14, weight: .semibold)).foregroundColor(.textPrimary)
                            Text(u.email).font(.system(size: 12)).foregroundColor(.textSecondary)
                            HStack(spacing: 6) {
                                Text(u.role.replacingOccurrences(of: "_", with: " ").uppercased())
                                    .font(.system(size: 9, weight: .bold))
                                    .foregroundColor(roleColor(u.role))
                                    .padding(.horizontal, 6).padding(.vertical, 2)
                                    .background(roleBg(u.role))
                                    .cornerRadius(4)
                                if let cn = u.companyName {
                                    Text(cn).font(.system(size: 11)).foregroundColor(.textSecondary)
                                }
                            }
                        }
                        Spacer()
                        Button {
                            editingUser = u
                            showForm = true
                        } label: {
                            Image(systemName: "pencil").font(.system(size: 14)).foregroundColor(.blue600)
                        }
                    }
                    .padding(.vertical, 4)
                }
                .listStyle(.plain)
                .refreshable { await loadUsers() }
            }
        }
        .background(Color.bgMain)
        .navigationBarHidden(true)
        .task { await loadUsers() }
        .sheet(isPresented: $showForm) {
            UserFormSheet(editing: editingUser, companyId: auth.companyId ?? 0, isSuperAdmin: auth.isSuperAdmin) {
                Task { await loadUsers() }
            }
        }
    }
    
    private func roleColor(_ role: String) -> Color {
        switch role {
        case "super_admin": return .red600
        case "admin": return .purple700
        default: return .blue600
        }
    }
    
    private func roleBg(_ role: String) -> Color {
        switch role {
        case "super_admin": return .red50
        case "admin": return .purple50
        default: return .blue50
        }
    }
    
    private func loadUsers() async {
        users = (try? await APIService.shared.getUsers(companyId: auth.isSuperAdmin ? auth.companyId : nil)) ?? []
        isLoading = false
    }
}

struct UserFormSheet: View {
    let editing: UserItem?
    let companyId: Int
    let isSuperAdmin: Bool
    let onSave: () -> Void
    @Environment(\.dismiss) var dismiss
    @State private var fullName = ""
    @State private var email = ""
    @State private var password = ""
    @State private var role = "user"
    @State private var isSaving = false
    
    private var roles: [String] {
        isSuperAdmin ? ["user", "admin", "super_admin"] : ["user", "admin"]
    }
    
    var body: some View {
        NavigationStack {
            Form {
                TextField("Full Name", text: $fullName)
                TextField("Email", text: $email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                SecureField(editing != nil ? "New Password (optional)" : "Password", text: $password)
                Picker("Role", selection: $role) {
                    ForEach(roles, id: \.self) { r in
                        Text(r.replacingOccurrences(of: "_", with: " ").capitalized).tag(r)
                    }
                }
            }
            .navigationTitle(editing != nil ? "Edit User" : "New User")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { save() } label: {
                        if isSaving { ProgressView() } else { Text("Save").fontWeight(.semibold) }
                    }
                    .disabled(fullName.isEmpty || email.isEmpty || isSaving)
                }
            }
            .onAppear {
                if let u = editing {
                    fullName = u.fullName; email = u.email; role = u.role
                }
            }
        }
    }
    
    private func save() {
        isSaving = true
        var data: [String: Any] = [
            "full_name": fullName, "email": email, "role": role, "company_id": companyId
        ]
        if !password.isEmpty { data["password"] = password }
        Task {
            do {
                if let u = editing {
                    _ = try await APIService.shared.updateUser(id: u.id, data: data)
                } else {
                    _ = try await APIService.shared.createUser(data: data)
                }
                onSave()
                await MainActor.run { dismiss() }
            } catch {}
            await MainActor.run { isSaving = false }
        }
    }
}
