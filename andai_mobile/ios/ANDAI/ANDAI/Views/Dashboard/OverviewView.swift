import SwiftUI

struct OverviewView: View {
    @EnvironmentObject var auth: AuthService
    @State private var docCount = 0
    @State private var faqCount = 0
    @State private var datasetCount = 0
    @State private var sessionCount = 0
    @State private var isLoading = true
    
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                // Welcome card
                VStack(alignment: .leading, spacing: 4) {
                    Text("Welcome back, \(auth.currentUser?.fullName.components(separatedBy: " ").first ?? "User")")
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(.white)
                    Text(auth.isSuperAdmin ? "Super Admin" : auth.currentUser?.companyName ?? "ANDAI Platform")
                        .font(.system(size: 13))
                        .foregroundColor(.slate400)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(24)
                .background(Color.sidebarBg)
                .cornerRadius(16)
                
                // Stats grid
                LazyVGrid(columns: [GridItem(.flexible()), GridItem(.flexible())], spacing: 12) {
                    StatCard(icon: "doc.text", label: "Documents", value: docCount, color: .blue600, bgColor: .blue50)
                    StatCard(icon: "questionmark.circle", label: "FAQ Items", value: faqCount, color: .amber600, bgColor: .amber50)
                    StatCard(icon: "server.rack", label: "Datasets", value: datasetCount, color: .emerald600, bgColor: .emerald50)
                    StatCard(icon: "bubble.left.and.bubble.right", label: "Chat Sessions", value: sessionCount, color: .purple700, bgColor: .purple50)
                }
                
                // Info cards
                InfoCard(
                    icon: "info.circle",
                    iconColor: .blue600,
                    title: "Quick Start",
                    text: "Use the Assistant tab to ask questions about your documents, databases, and FAQ. Upload documents, manage FAQ items, and explore datasets from the Manage tab."
                )
                
                InfoCard(
                    icon: "cpu",
                    iconColor: .appPrimary,
                    title: "AI-Powered Insights",
                    text: "ANDAI uses local LLM models via Ollama to provide intelligent answers from your data. Toggle between Instant, Auto, and Thinking modes for different response speeds."
                )
            }
            .padding(16)
        }
        .background(Color.bgMain)
        .navigationTitle("Home")
        .refreshable { await loadStats() }
        .task { await loadStats() }
    }
    
    private func loadStats() async {
        guard let cid = auth.companyId else { isLoading = false; return }
        async let docs = APIService.shared.getDocuments(companyId: cid)
        async let faqs = APIService.shared.getFAQ(companyId: cid)
        async let datasets = APIService.shared.getDatasets(companyId: cid)
        async let sessions = APIService.shared.getChatSessions(companyId: cid)
        
        docCount = (try? await docs.count) ?? 0
        faqCount = (try? await faqs.count) ?? 0
        datasetCount = (try? await datasets.count) ?? 0
        sessionCount = (try? await sessions.count) ?? 0
        isLoading = false
    }
}

struct StatCard: View {
    let icon: String
    let label: String
    let value: Int
    let color: Color
    let bgColor: Color
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            ZStack {
                RoundedRectangle(cornerRadius: 10)
                    .fill(bgColor)
                    .frame(width: 40, height: 40)
                Image(systemName: icon)
                    .font(.system(size: 18))
                    .foregroundColor(color)
            }
            Text("\(value)")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(.textPrimary)
            Text(label)
                .font(.system(size: 13))
                .foregroundColor(.textSecondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color.bgCard)
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.border, lineWidth: 1)
        )
    }
}

struct InfoCard: View {
    let icon: String
    let iconColor: Color
    let title: String
    let text: String
    
    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .foregroundColor(iconColor)
                Text(title)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.textPrimary)
            }
            Text(text)
                .font(.system(size: 13))
                .foregroundColor(.textSecondary)
                .lineSpacing(4)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(Color.bgCard)
        .cornerRadius(16)
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.border, lineWidth: 1)
        )
    }
}
