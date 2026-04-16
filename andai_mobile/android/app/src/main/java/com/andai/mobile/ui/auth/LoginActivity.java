package com.andai.mobile.ui.auth;

import android.content.Intent;
import android.os.Bundle;
import android.text.InputType;
import android.text.TextUtils;
import android.view.View;
import android.view.inputmethod.EditorInfo;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;

import com.andai.mobile.R;
import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.ActivityLoginBinding;
import com.andai.mobile.models.LoginResponse;
import com.andai.mobile.ui.dashboard.MainActivity;
import com.andai.mobile.utils.AuthManager;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;

public class LoginActivity extends AppCompatActivity {

    private ActivityLoginBinding binding;
    private boolean passwordVisible;

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        AuthManager auth = AuthManager.getInstance(this);
        if (auth.isLoggedIn()) {
            startActivity(new Intent(this, MainActivity.class));
            finish();
            return;
        }

        ApiClient.getInstance().setAuthManager(auth);

        binding = ActivityLoginBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        binding.etPassword.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == EditorInfo.IME_ACTION_DONE) {
                attemptLogin();
                return true;
            }
            return false;
        });

        binding.ivTogglePassword.setOnClickListener(v -> togglePasswordVisibility());

        binding.btnLogin.setOnClickListener(v -> attemptLogin());
    }

    private void togglePasswordVisibility() {
        passwordVisible = !passwordVisible;
        int end = binding.etPassword.getText() != null
                ? binding.etPassword.getSelectionEnd()
                : 0;
        if (passwordVisible) {
            binding.etPassword.setInputType(
                    InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD);
            binding.ivTogglePassword.setImageResource(R.drawable.ic_eye_off);
        } else {
            binding.etPassword.setInputType(
                    InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
            binding.ivTogglePassword.setImageResource(R.drawable.ic_eye);
        }
        binding.etPassword.setTypeface(binding.etPassword.getTypeface());
        if (end >= 0) {
            binding.etPassword.setSelection(Math.min(end, binding.etPassword.getText().length()));
        }
    }

    private void attemptLogin() {
        binding.tvError.setVisibility(View.GONE);

        String email = binding.etEmail.getText() != null
                ? binding.etEmail.getText().toString().trim()
                : "";
        String password = binding.etPassword.getText() != null
                ? binding.etPassword.getText().toString()
                : "";

        if (TextUtils.isEmpty(email) || TextUtils.isEmpty(password)) {
            showError("Please enter email and password.");
            return;
        }

        setLoading(true);

        ApiClient.getInstance().login(email, password, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                try {
                    LoginResponse loginResponse = new Gson().fromJson(responseBody, LoginResponse.class);
                    if (loginResponse == null
                            || loginResponse.accessToken == null
                            || loginResponse.user == null) {
                        setLoading(false);
                        showError("Invalid server response.");
                        return;
                    }
                    AuthManager.getInstance(LoginActivity.this)
                            .saveSession(loginResponse.accessToken, loginResponse.user);
                    setLoading(false);
                    startActivity(new Intent(LoginActivity.this, MainActivity.class));
                    finish();
                } catch (JsonSyntaxException e) {
                    setLoading(false);
                    showError("Could not parse login response.");
                }
            }

            @Override
            public void onError(String error) {
                setLoading(false);
                showError(error != null ? error : "Login failed.");
            }
        });
    }

    private void setLoading(boolean loading) {
        binding.progressLogin.setVisibility(loading ? View.VISIBLE : View.GONE);
        binding.btnLogin.setEnabled(!loading);
        binding.btnLogin.setText(loading ? "" : "Sign in");
        binding.etEmail.setEnabled(!loading);
        binding.etPassword.setEnabled(!loading);
        binding.ivTogglePassword.setEnabled(!loading);
    }

    private void showError(String message) {
        binding.tvError.setText(message);
        binding.tvError.setVisibility(View.VISIBLE);
    }
}
