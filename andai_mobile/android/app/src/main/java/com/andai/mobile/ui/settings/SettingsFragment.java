package com.andai.mobile.ui.settings;

import android.content.Intent;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;

import com.andai.mobile.BuildConfig;
import com.andai.mobile.R;
import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.FragmentSettingsBinding;
import com.andai.mobile.models.CompanyItem;
import com.andai.mobile.models.User;
import com.andai.mobile.ui.auth.LoginActivity;
import com.andai.mobile.utils.AuthManager;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.gson.Gson;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class SettingsFragment extends Fragment {

    private FragmentSettingsBinding binding;
    private final Gson gson = new Gson();

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentSettingsBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        refreshProfile();

        AuthManager auth = AuthManager.getInstance(requireContext());
        binding.btnSwitchCompany.setVisibility(auth.isSuperAdmin() ? View.VISIBLE : View.GONE);
        binding.btnSwitchCompany.setOnClickListener(v -> showCompanyPicker());

        binding.btnServerStatus.setOnClickListener(v -> checkServerStatus());
        binding.btnLogout.setOnClickListener(v -> logout());

        binding.tvAbout.setText(getString(R.string.settings_about_body_detail, BuildConfig.VERSION_NAME, BuildConfig.API_BASE_URL));
    }

    @Override
    public void onResume() {
        super.onResume();
        refreshProfile();
    }

    private void refreshProfile() {
        AuthManager auth = AuthManager.getInstance(requireContext());
        User u = auth.getUser();
        if (u == null) return;

        String name = !TextUtils.isEmpty(u.fullName) ? u.fullName : u.email;
        binding.tvProfileName.setText(name);
        binding.tvProfileEmail.setText(u.email != null ? u.email : "");
        binding.tvProfileRole.setText(u.role != null ? u.role : "");

        String initial = "?";
        if (!TextUtils.isEmpty(u.fullName)) {
            initial = u.fullName.substring(0, 1).toUpperCase();
        } else if (!TextUtils.isEmpty(u.email)) {
            initial = u.email.substring(0, 1).toUpperCase();
        }
        binding.tvProfileInitial.setText(initial);

        String companyLine = !TextUtils.isEmpty(u.companyName) ? u.companyName : "";
        if (auth.getCompanyId() != null) {
            companyLine = companyLine + " (ID " + auth.getCompanyId() + ")";
        }
        binding.tvCurrentCompany.setText(companyLine);
    }

    private void showCompanyPicker() {
        binding.progressStatus.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getCompanies(new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progressStatus.setVisibility(View.GONE);
                try {
                    Type type = new TypeToken<List<CompanyItem>>() {
                    }.getType();
                    List<CompanyItem> list = gson.fromJson(responseBody, type);
                    if (list == null) list = new ArrayList<>();
                    if (list.isEmpty()) {
                        Toast.makeText(requireContext(), R.string.no_companies, Toast.LENGTH_SHORT).show();
                        return;
                    }
                    String[] labels = new String[list.size()];
                    for (int i = 0; i < list.size(); i++) {
                        CompanyItem c = list.get(i);
                        labels[i] = c.name + (c.isActive ? "" : " (inactive)");
                    }
                    new MaterialAlertDialogBuilder(requireContext())
                            .setTitle(R.string.settings_switch_company)
                            .setItems(labels, (d, which) -> {
                                CompanyItem picked = list.get(which);
                                AuthManager.getInstance(requireContext()).setCompanyId(picked.id);
                                refreshProfile();
                                Toast.makeText(requireContext(), R.string.company_switched, Toast.LENGTH_SHORT).show();
                            })
                            .setNegativeButton(R.string.cancel, null)
                            .show();
                } catch (JsonSyntaxException e) {
                    Toast.makeText(requireContext(), R.string.error_parse, Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progressStatus.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void checkServerStatus() {
        binding.tvServerStatus.setVisibility(View.GONE);
        binding.progressStatus.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getStatus(new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progressStatus.setVisibility(View.GONE);
                binding.tvServerStatus.setVisibility(View.VISIBLE);
                binding.tvServerStatus.setText(responseBody);
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progressStatus.setVisibility(View.GONE);
                binding.tvServerStatus.setVisibility(View.VISIBLE);
                binding.tvServerStatus.setText(error);
            }
        });
    }

    private void logout() {
        AuthManager.getInstance(requireContext()).logout();
        Intent i = new Intent(requireContext(), LoginActivity.class);
        i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
        startActivity(i);
        requireActivity().finish();
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }
}
