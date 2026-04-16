import Foundation
import SwiftUI

class AuthService: ObservableObject {
    static let shared = AuthService()
    
    @Published var currentUser: User?
    @Published var isAuthenticated = false
    @Published var isLoading = true
    @Published var selectedCompanyId: Int?
    
    var token: String? {
        get { KeychainHelper.get(key: "auth_token") }
        set {
            if let val = newValue { KeychainHelper.save(key: "auth_token", value: val) }
            else { KeychainHelper.delete(key: "auth_token") }
        }
    }
    
    var isAdmin: Bool { currentUser?.isAdmin ?? false }
    var isSuperAdmin: Bool { currentUser?.isSuperAdmin ?? false }
    
    var companyId: Int? {
        selectedCompanyId ?? currentUser?.companyId
    }
    
    private init() {
        loadStoredSession()
    }
    
    func loadStoredSession() {
        isLoading = true
        if let token = token, !token.isEmpty,
           let userData = UserDefaults.standard.data(forKey: "user_data"),
           let user = try? JSONDecoder().decode(User.self, from: userData) {
            self.currentUser = user
            self.isAuthenticated = true
            self.selectedCompanyId = UserDefaults.standard.object(forKey: "selected_company_id") as? Int ?? user.companyId
        }
        isLoading = false
    }
    
    func login(email: String, password: String) async throws {
        let response = try await APIService.shared.login(email: email, password: password)
        
        await MainActor.run {
            self.token = response.accessToken
            self.currentUser = response.user
            self.isAuthenticated = true
            self.selectedCompanyId = response.user.companyId
            
            if let data = try? JSONEncoder().encode(response.user) {
                UserDefaults.standard.set(data, forKey: "user_data")
            }
        }
    }
    
    func logout() {
        token = nil
        UserDefaults.standard.removeObject(forKey: "user_data")
        UserDefaults.standard.removeObject(forKey: "selected_company_id")
        
        DispatchQueue.main.async {
            self.currentUser = nil
            self.isAuthenticated = false
            self.selectedCompanyId = nil
        }
    }
    
    func setCompanyId(_ id: Int) {
        selectedCompanyId = id
        UserDefaults.standard.set(id, forKey: "selected_company_id")
    }
}

// MARK: - Keychain Helper

enum KeychainHelper {
    static func save(key: String, value: String) {
        let data = value.data(using: .utf8)!
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
        
        var newItem = query
        newItem[kSecValueData as String] = data
        SecItemAdd(newItem as CFDictionary, nil)
    }
    
    static func get(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        SecItemCopyMatching(query as CFDictionary, &result)
        guard let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }
    
    static func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
