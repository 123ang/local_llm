package com.andai.mobile.ui.dashboard;

import android.content.Intent;
import android.os.Bundle;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;

import com.andai.mobile.R;
import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.ActivityMainBinding;
import com.andai.mobile.ui.assistant.AssistantFragment;
import com.andai.mobile.ui.auth.LoginActivity;
import com.andai.mobile.ui.settings.SettingsFragment;
import com.andai.mobile.utils.AuthManager;
import com.google.android.material.navigation.NavigationBarView;

public class MainActivity extends AppCompatActivity {

    private ActivityMainBinding binding;
    private AuthManager authManager;

    private final OverviewFragment overviewFragment = new OverviewFragment();
    private final AssistantFragment assistantFragment = new AssistantFragment();
    private final ManageFragment manageFragment = new ManageFragment();
    private final SettingsFragment settingsFragment = new SettingsFragment();

    @Override
    protected void onCreate(@Nullable Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        authManager = AuthManager.getInstance(this);
        if (!authManager.isLoggedIn()) {
            startActivity(new Intent(this, LoginActivity.class));
            finish();
            return;
        }

        ApiClient.getInstance().setAuthManager(authManager);

        binding = ActivityMainBinding.inflate(getLayoutInflater());
        setContentView(binding.getRoot());

        configureManageTabVisibility();

        binding.bottomNav.setOnItemSelectedListener(navListener);

        if (savedInstanceState == null) {
            getSupportFragmentManager()
                    .beginTransaction()
                    .replace(R.id.fragment_container, overviewFragment)
                    .commit();
            binding.bottomNav.setSelectedItemId(R.id.nav_home);
        }

        getSupportFragmentManager().addOnBackStackChangedListener(this::onBackStackChanged);
    }

    @Override
    protected void onResume() {
        super.onResume();
        configureManageTabVisibility();
    }

    private void configureManageTabVisibility() {
        boolean admin = authManager.isAdmin();
        binding.bottomNav.getMenu().findItem(R.id.nav_manage).setVisible(admin);
    }

    private final NavigationBarView.OnItemSelectedListener navListener =
            item -> {
                int id = item.getItemId();
                if (id == R.id.nav_home) {
                    showRootFragment(overviewFragment);
                    return true;
                }
                if (id == R.id.nav_assistant) {
                    showRootFragment(assistantFragment);
                    return true;
                }
                if (id == R.id.nav_manage) {
                    showRootFragment(manageFragment);
                    return true;
                }
                if (id == R.id.nav_settings) {
                    showRootFragment(settingsFragment);
                    return true;
                }
                return false;
            };

    private void showRootFragment(@NonNull Fragment fragment) {
        FragmentManager fm = getSupportFragmentManager();
        fm.popBackStack(null, FragmentManager.POP_BACK_STACK_INCLUSIVE);
        fm.beginTransaction()
                .replace(R.id.fragment_container, fragment)
                .commit();
    }

    private void onBackStackChanged() {
        FragmentManager fm = getSupportFragmentManager();
        Fragment f = fm.findFragmentById(R.id.fragment_container);
        if (f == null) {
            return;
        }
        if (fm.getBackStackEntryCount() > 0) {
            return;
        }
        if (f instanceof OverviewFragment) {
            binding.bottomNav.setSelectedItemId(R.id.nav_home);
        } else if (f instanceof AssistantFragment) {
            binding.bottomNav.setSelectedItemId(R.id.nav_assistant);
        } else if (f instanceof ManageFragment) {
            binding.bottomNav.setSelectedItemId(R.id.nav_manage);
        } else if (f instanceof SettingsFragment) {
            binding.bottomNav.setSelectedItemId(R.id.nav_settings);
        }
    }

    @SuppressWarnings("deprecation")
    @Override
    public void onBackPressed() {
        FragmentManager fm = getSupportFragmentManager();
        if (fm.getBackStackEntryCount() > 0) {
            fm.popBackStack();
            return;
        }
        super.onBackPressed();
    }
}
