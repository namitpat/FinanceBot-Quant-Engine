Rails.application.routes.draw do
  resources :watchlists, only: %i[index show create update destroy] do
    get :performance, on: :member
  end
end
