import SwiftUI

struct MainTabView: View {
    @EnvironmentObject var auth: AuthService
    
    var body: some View {
        TabView {
            NavigationStack {
                OverviewView()
            }
            .tabItem {
                Label("Home", systemImage: "house")
            }
            
            NavigationStack {
                AssistantView()
            }
            .tabItem {
                Label("Assistant", systemImage: "bubble.left.and.bubble.right")
            }
            
            if auth.isAdmin {
                NavigationStack {
                    ManageView()
                }
                .tabItem {
                    Label("Manage", systemImage: "square.grid.2x2")
                }
            }
            
            NavigationStack {
                SettingsView()
            }
            .tabItem {
                Label("Settings", systemImage: "gearshape")
            }
        }
        .tint(.appPrimary)
    }
}

struct ManageView: View {
    @EnvironmentObject var auth: AuthService
    
    var body: some View {
        List {
            if auth.isAdmin {
                Section("Administration") {
                    NavigationLink {
                        DocumentsView()
                    } label: {
                        Label {
                            VStack(alignment: .leading) {
                                Text("Documents")
                                    .font(.system(size: 15, weight: .medium))
                                Text("Upload and manage PDFs")
                                    .font(.system(size: 12))
                                    .foregroundColor(.textSecondary)
                            }
                        } icon: {
                            Image(systemName: "doc.text")
                                .foregroundColor(.blue600)
                        }
                    }
                    
                    NavigationLink {
                        FAQListView()
                    } label: {
                        Label {
                            VStack(alignment: .leading) {
                                Text("FAQ")
                                    .font(.system(size: 15, weight: .medium))
                                Text("Manage FAQ items")
                                    .font(.system(size: 12))
                                    .foregroundColor(.textSecondary)
                            }
                        } icon: {
                            Image(systemName: "questionmark.circle")
                                .foregroundColor(.amber600)
                        }
                    }
                    
                    NavigationLink {
                        DatabaseView()
                    } label: {
                        Label {
                            VStack(alignment: .leading) {
                                Text("Database")
                                    .font(.system(size: 15, weight: .medium))
                                Text("Browse datasets")
                                    .font(.system(size: 12))
                                    .foregroundColor(.textSecondary)
                            }
                        } icon: {
                            Image(systemName: "server.rack")
                                .foregroundColor(.emerald600)
                        }
                    }
                }
            }
            
            if auth.isSuperAdmin {
                Section("Platform") {
                    NavigationLink {
                        CompaniesView()
                    } label: {
                        Label {
                            VStack(alignment: .leading) {
                                Text("Companies")
                                    .font(.system(size: 15, weight: .medium))
                                Text("Manage tenants")
                                    .font(.system(size: 12))
                                    .foregroundColor(.textSecondary)
                            }
                        } icon: {
                            Image(systemName: "building.2")
                                .foregroundColor(.appPrimary)
                        }
                    }
                    
                    NavigationLink {
                        UsersView()
                    } label: {
                        Label {
                            VStack(alignment: .leading) {
                                Text("Users")
                                    .font(.system(size: 15, weight: .medium))
                                Text("Manage users")
                                    .font(.system(size: 12))
                                    .foregroundColor(.textSecondary)
                            }
                        } icon: {
                            Image(systemName: "person.2")
                                .foregroundColor(.purple700)
                        }
                    }
                    
                    NavigationLink {
                        AuditView()
                    } label: {
                        Label {
                            VStack(alignment: .leading) {
                                Text("Audit Logs")
                                    .font(.system(size: 15, weight: .medium))
                                Text("Activity history")
                                    .font(.system(size: 12))
                                    .foregroundColor(.textSecondary)
                            }
                        } icon: {
                            Image(systemName: "doc.plaintext")
                                .foregroundColor(.slate600)
                        }
                    }
                }
            }
        }
        .navigationTitle("Manage")
    }
}
