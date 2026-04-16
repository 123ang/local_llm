import SwiftUI

struct LoginView: View {
    @EnvironmentObject var auth: AuthService
    @State private var email = ""
    @State private var password = ""
    @State private var showPassword = false
    @State private var isLoading = false
    @State private var errorMessage = ""
    
    var body: some View {
        ZStack {
            LinearGradient(
                colors: [.sidebarBg, .sidebarHover, .deepBlue],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            
            ScrollView {
                VStack(spacing: 0) {
                    Spacer().frame(height: 80)
                    
                    // Logo
                    VStack(spacing: 16) {
                        ZStack {
                            RoundedRectangle(cornerRadius: 20)
                                .fill(.white)
                                .frame(width: 80, height: 80)
                                .shadow(color: .black.opacity(0.3), radius: 8, y: 4)
                            
                            Image(systemName: "cpu")
                                .font(.system(size: 36))
                                .foregroundColor(.appPrimary)
                        }
                        
                        VStack(spacing: 2) {
                            Text("Adaptive Neural")
                                .font(.system(size: 26, weight: .bold))
                            Text("Decision AI")
                                .font(.system(size: 26, weight: .bold))
                        }
                        .foregroundColor(.white)
                        
                        Text("ANDAI")
                            .font(.system(size: 13, weight: .semibold))
                            .foregroundColor(.slate400)
                            .tracking(4)
                    }
                    .padding(.bottom, 32)
                    
                    // Form
                    VStack(spacing: 20) {
                        if !errorMessage.isEmpty {
                            HStack {
                                Text(errorMessage)
                                    .font(.system(size: 13))
                                    .foregroundColor(Color(hex: "fca5a5"))
                            }
                            .padding(12)
                            .background(Color.red.opacity(0.2))
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.red.opacity(0.3), lineWidth: 1)
                            )
                            .cornerRadius(12)
                        }
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Email")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(.slate300)
                            
                            TextField("", text: $email, prompt: Text("admin@askai.local").foregroundColor(.white.opacity(0.3)))
                                .textInputAutocapitalization(.never)
                                .autocorrectionDisabled()
                                .keyboardType(.emailAddress)
                                .padding(14)
                                .background(Color.white.opacity(0.1))
                                .cornerRadius(12)
                                .overlay(
                                    RoundedRectangle(cornerRadius: 12)
                                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                                )
                                .foregroundColor(.white)
                        }
                        
                        VStack(alignment: .leading, spacing: 8) {
                            Text("Password")
                                .font(.system(size: 13, weight: .medium))
                                .foregroundColor(.slate300)
                            
                            HStack {
                                Group {
                                    if showPassword {
                                        TextField("", text: $password, prompt: Text("Enter your password").foregroundColor(.white.opacity(0.3)))
                                    } else {
                                        SecureField("", text: $password, prompt: Text("Enter your password").foregroundColor(.white.opacity(0.3)))
                                    }
                                }
                                .textInputAutocapitalization(.never)
                                .foregroundColor(.white)
                                
                                Button {
                                    showPassword.toggle()
                                } label: {
                                    Image(systemName: showPassword ? "eye.slash" : "eye")
                                        .foregroundColor(.white.opacity(0.5))
                                        .font(.system(size: 16))
                                }
                            }
                            .padding(14)
                            .background(Color.white.opacity(0.1))
                            .cornerRadius(12)
                            .overlay(
                                RoundedRectangle(cornerRadius: 12)
                                    .stroke(Color.white.opacity(0.2), lineWidth: 1)
                            )
                        }
                        
                        Button {
                            performLogin()
                        } label: {
                            Group {
                                if isLoading {
                                    ProgressView()
                                        .tint(.white)
                                } else {
                                    Text("Sign in")
                                        .font(.system(size: 16, weight: .semibold))
                                }
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                            .background(Color.appPrimary)
                            .foregroundColor(.white)
                            .cornerRadius(12)
                            .shadow(color: .appPrimary.opacity(0.3), radius: 8, y: 4)
                        }
                        .disabled(isLoading)
                        .opacity(isLoading ? 0.6 : 1)
                        
                        Text("Default: admin@askai.local / admin123")
                            .font(.system(size: 11))
                            .foregroundColor(.slate500)
                            .frame(maxWidth: .infinity)
                    }
                    .padding(24)
                    .background(Color.white.opacity(0.1))
                    .cornerRadius(20)
                    .overlay(
                        RoundedRectangle(cornerRadius: 20)
                            .stroke(Color.white.opacity(0.2), lineWidth: 1)
                    )
                    .padding(.horizontal, 24)
                    
                    Spacer()
                }
            }
        }
    }
    
    private func performLogin() {
        guard !email.isEmpty, !password.isEmpty else { return }
        errorMessage = ""
        isLoading = true
        
        Task {
            do {
                try await auth.login(email: email, password: password)
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                }
            }
            await MainActor.run { isLoading = false }
        }
    }
}
