package com.andai.mobile.ui.users;

import android.os.Bundle;
import android.text.TextUtils;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.fragment.app.Fragment;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.andai.mobile.R;
import com.andai.mobile.api.ApiClient;
import com.andai.mobile.databinding.FragmentUsersBinding;
import com.andai.mobile.databinding.ItemUserBinding;
import com.andai.mobile.models.AdminUser;
import com.andai.mobile.utils.AuthManager;
import com.google.android.material.dialog.MaterialAlertDialogBuilder;
import com.google.android.material.switchmaterial.SwitchMaterial;
import com.google.android.material.textfield.TextInputEditText;
import com.google.gson.Gson;
import com.google.gson.JsonObject;
import com.google.gson.JsonSyntaxException;
import com.google.gson.reflect.TypeToken;

import java.lang.reflect.Type;
import java.util.ArrayList;
import java.util.List;

public class UsersFragment extends Fragment {

    private FragmentUsersBinding binding;
    private final Gson gson = new Gson();
    private final List<AdminUser> items = new ArrayList<>();
    private UserAdapter adapter;

    @Nullable
    @Override
    public View onCreateView(@NonNull LayoutInflater inflater, @Nullable ViewGroup container,
                             @Nullable Bundle savedInstanceState) {
        binding = FragmentUsersBinding.inflate(inflater, container, false);
        return binding.getRoot();
    }

    @Override
    public void onViewCreated(@NonNull View view, @Nullable Bundle savedInstanceState) {
        super.onViewCreated(view, savedInstanceState);
        adapter = new UserAdapter();
        binding.rvUsers.setLayoutManager(new LinearLayoutManager(requireContext()));
        binding.rvUsers.setAdapter(adapter);

        binding.btnAdd.setOnClickListener(v -> showUserDialog(null));
        loadUsers();
    }

    private void loadUsers() {
        AuthManager auth = AuthManager.getInstance(requireContext());
        Integer companyId = auth.isSuperAdmin() ? null : auth.getCompanyId();

        binding.progress.setVisibility(View.VISIBLE);
        ApiClient.getInstance().getUsers(companyId, new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                try {
                    Type type = new TypeToken<List<AdminUser>>() {
                    }.getType();
                    List<AdminUser> list = gson.fromJson(responseBody, type);
                    items.clear();
                    if (list != null) {
                        items.addAll(list);
                    }
                    adapter.notifyDataSetChanged();
                } catch (JsonSyntaxException e) {
                    Toast.makeText(requireContext(), R.string.error_parse, Toast.LENGTH_SHORT).show();
                }
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void showUserDialog(@Nullable AdminUser existing) {
        AuthManager auth = AuthManager.getInstance(requireContext());
        View form = getLayoutInflater().inflate(R.layout.dialog_user_form, null);
        TextInputEditText etEmail = form.findViewById(R.id.etEmail);
        TextInputEditText etName = form.findViewById(R.id.etFullName);
        TextInputEditText etPass = form.findViewById(R.id.etPassword);
        TextInputEditText etRole = form.findViewById(R.id.etRole);
        TextInputEditText etCompanyId = form.findViewById(R.id.etCompanyId);
        View layoutCompanyId = form.findViewById(R.id.layoutCompanyId);
        SwitchMaterial swActive = form.findViewById(R.id.swActive);

        layoutCompanyId.setVisibility(auth.isSuperAdmin() ? View.VISIBLE : View.GONE);

        if (existing != null) {
            etEmail.setText(existing.email);
            etEmail.setEnabled(false);
            etName.setText(existing.fullName);
            etRole.setText(existing.role);
            etPass.setHint(R.string.password_optional);
            if (existing.companyId != null && auth.isSuperAdmin()) {
                etCompanyId.setText(String.valueOf(existing.companyId));
            }
            swActive.setVisibility(View.VISIBLE);
            swActive.setChecked(existing.isActive);
        } else {
            if (auth.getCompanyId() != null && !auth.isSuperAdmin()) {
                etCompanyId.setText(String.valueOf(auth.getCompanyId()));
            }
        }

        new MaterialAlertDialogBuilder(requireContext())
                .setTitle(existing == null ? R.string.add : R.string.edit)
                .setView(form)
                .setPositiveButton(R.string.save, (d, w) -> {
                    String email = text(etEmail);
                    String fullName = text(etName);
                    String role = text(etRole);
                    if (TextUtils.isEmpty(role)) {
                        role = "user";
                    }
                    if (TextUtils.isEmpty(email) || TextUtils.isEmpty(fullName)) {
                        Toast.makeText(requireContext(), R.string.error_required_fields, Toast.LENGTH_SHORT).show();
                        return;
                    }

                    binding.progress.setVisibility(View.VISIBLE);
                    if (existing == null) {
                        String password = text(etPass);
                        if (TextUtils.isEmpty(password)) {
                            binding.progress.setVisibility(View.GONE);
                            Toast.makeText(requireContext(), R.string.password_required_new, Toast.LENGTH_SHORT).show();
                            return;
                        }
                        JsonObject json = new JsonObject();
                        json.addProperty("email", email);
                        json.addProperty("full_name", fullName);
                        json.addProperty("password", password);
                        json.addProperty("role", role);
                        if (auth.isSuperAdmin()) {
                            String cid = text(etCompanyId);
                            if (!TextUtils.isEmpty(cid)) {
                                try {
                                    json.addProperty("company_id", Integer.parseInt(cid));
                                } catch (NumberFormatException ignored) {
                                }
                            }
                        } else if (auth.getCompanyId() != null) {
                            json.addProperty("company_id", auth.getCompanyId());
                        }
                        ApiClient.getInstance().createUser(json.toString(), callbackAfterSave());
                    } else {
                        JsonObject json = new JsonObject();
                        json.addProperty("full_name", fullName);
                        json.addProperty("role", role);
                        json.addProperty("is_active", swActive.isChecked());
                        if (auth.isSuperAdmin()) {
                            String cid = text(etCompanyId);
                            if (!TextUtils.isEmpty(cid)) {
                                try {
                                    json.addProperty("company_id", Integer.parseInt(cid));
                                } catch (NumberFormatException ignored) {
                                }
                            }
                        }
                        ApiClient.getInstance().updateUser(existing.id, json.toString(), callbackAfterSave());
                    }
                })
                .setNegativeButton(R.string.cancel, null)
                .show();
    }

    private String text(TextInputEditText et) {
        CharSequence cs = et.getText();
        return cs != null ? cs.toString().trim() : "";
    }

    private ApiClient.ApiCallback callbackAfterSave() {
        return new ApiClient.ApiCallback() {
            @Override
            public void onSuccess(String responseBody) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                loadUsers();
            }

            @Override
            public void onError(String error) {
                if (!isAdded()) return;
                binding.progress.setVisibility(View.GONE);
                Toast.makeText(requireContext(), error, Toast.LENGTH_SHORT).show();
            }
        };
    }

    private static String initial(String fullName, String email) {
        if (!TextUtils.isEmpty(fullName)) {
            return fullName.substring(0, 1).toUpperCase();
        }
        if (!TextUtils.isEmpty(email)) {
            return email.substring(0, 1).toUpperCase();
        }
        return "?";
    }

    @Override
    public void onDestroyView() {
        super.onDestroyView();
        binding = null;
    }

    private class UserAdapter extends RecyclerView.Adapter<Uh> {

        @NonNull
        @Override
        public Uh onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
            ItemUserBinding b = ItemUserBinding.inflate(getLayoutInflater(), parent, false);
            return new Uh(b);
        }

        @Override
        public void onBindViewHolder(@NonNull Uh holder, int position) {
            AdminUser u = items.get(position);
            holder.b.tvInitial.setText(initial(u.fullName, u.email));
            holder.b.tvName.setText(u.fullName);
            holder.b.tvEmail.setText(u.email);
            holder.b.tvRole.setText(u.role);
            holder.b.tvCompany.setText(!TextUtils.isEmpty(u.companyName) ? u.companyName : "—");
            holder.b.btnEdit.setOnClickListener(v -> showUserDialog(u));
        }

        @Override
        public int getItemCount() {
            return items.size();
        }
    }

    static class Uh extends RecyclerView.ViewHolder {
        final ItemUserBinding b;

        Uh(ItemUserBinding b) {
            super(b.getRoot());
            this.b = b;
        }
    }
}
