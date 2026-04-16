import SwiftUI

@main
struct ANDAIApp: App {
    @StateObject private var auth = AuthService.shared
    
    var body: some Scene {
        WindowGroup {
            Group {
                if auth.isLoading {
                    LoadingView()
                } else if auth.isAuthenticated {
                    MainTabView()
                        .environmentObject(auth)
                } else {
                    LoginView()
                        .environmentObject(auth)
                }
            }
            .animation(.easeInOut, value: auth.isAuthenticated)
        }
    }
}

struct LoadingView: View {
    var body: some View {
        ZStack {
            Color.bgMain.ignoresSafeArea()
            ProgressView()
                .tint(.appPrimary)
                .scaleEffect(1.5)
        }
    }
}
